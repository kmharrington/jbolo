import os
import copy
import yaml

import numpy as np
from numpy.polynomial.polynomial import polyval

import jbolo.jbolo_funcs as jf
import jbolo.utils as utils
from jbolo.utils import load_sim


def apply_telescope_configs(sim, configs):
    sim['bolo_config']['T_bath'] = configs.get(
        "T_bath", sim['bolo_config']['T_bath']
    )

def apply_pwv( ch_cfgs, pwv, sin_el):
    assert len(ch_cfgs['P_opt']) == 2, "P_opt not written as linear equation"
    ch_cfgs['P_opt'] = polyval(pwv/sin_el, ch_cfgs['P_opt'] ) 

def apply_psat( ch_cfgs, T_bath, T_c):
    n = ch_cfgs['n']
    kappa = ch_cfgs['kappa']

    ch_cfgs['psat'] = kappa*(T_c**n - T_bath**n)

def apply_Gdynamic(ch_cfgs, T_bath, T_c):
    n = ch_cfgs['n']
    psat = ch_cfgs['psat']

    ch_cfgs['G_dynamic'] = psat*n * T_c**(n-1)/(T_c**n - T_bath**n)

def apply_wafer_configs(sim, configs, wafer, update_det_params=True):
    """
    apply per wafer configurations, these configs are in the form:
    note that the per channel configs are updated directly into sim['channels']

    wafers:
      wafer_name:
        R_n: X             ## measured in UXM Dashboard
        T_c: X             ## measured in UXM Dashboard
        yield: X           ## measured in UXM Dashboard
        psat_tbath: X      ## the bath temperature where Psat was measured
        MF_X: (entry for MF_1 and MF_2)
          det_eff: X       ## measured adjusted for v4r1 passbands
          psat: X          ## measured in UXM Dashboard
          kappa: X         ## measured in UXM Dashboard
          G_dynamic: X      ## measured in UXM Dashboard
          n: X             ## measured in UXM Dashboard
          P_opt: ## measured as m*PWV/sin(el) + b
            - b
            - m 
          NEP_dark: X      ## measured in UXM Dashboard
          NEP_meas: X      ## measured in commissioning paper
          NEP_vib_shift: X ## shift in median noise due to high noise tails
          abscal_rj: 
            - X            ## measured in commissioning paper
            - sigma_x      ## measured in commissioning paper
          pton_det_eff: X  ## measured assuming v3r6 passbands
    """
    assert wafer in configs['wafers'], f"{wafer} not in configurations"
    wafer_configs = configs['wafers'][wafer]
    
    ## R_bolo assumed to be 0.5 R_n
    sim['bolo_config']['R_bolo'] = 0.5*wafer_configs.get(
        "R_n", 2*sim['bolo_config']['R_bolo']
    )
    sim['bolo_config']['yield'] = wafer_configs.get(
        "yield", sim['bolo_config']['yield']
    )
    sim['bolo_config']['T_c'] = wafer_configs.get(
        'T_c', sim['bolo_config']['T_c']
    )

    ## um to mm
    pwv = 1e-3*sim['sources']['atmosphere']['pwv']
    sin_el = np.sin( np.radians( sim['sources']['atmosphere']['elevation']))

    for ch in sim['channels']:
        assert ch in wafer_configs, f"{ch} not found in {wafer} configs"

        sim['channels'][ch].update( wafer_configs[ch] )
        apply_pwv( sim['channels'][ch], pwv, sin_el)
        if update_det_params:
            apply_psat( 
                sim['channels'][ch], 
                sim['bolo_config']['T_bath'],
                sim['bolo_config']['T_c']
            )
            sim['bolo_config']['psat_method'] = 'specified'
            apply_Gdynamic( 
                sim['channels'][ch], 
                sim['bolo_config']['T_bath'] ,
                sim['bolo_config']['T_c']
            )
            sim['bolo_config']['G_dynamic_method'] = 'specified'
            

def run_wafer(
        sim_file, configs, wafer, additional_functions=[],
        wafer_kwargs={}
    ):
    sim = utils.load_sim( sim_file )
    apply_telescope_configs(sim, configs)
    apply_wafer_configs(sim, configs, wafer, **wafer_kwargs)
    sim['version']['wafer'] = wafer

    for func in additional_functions:
        func(sim)

    jf.run_optics(sim)
    jf.run_bolos(sim)
    return sim

