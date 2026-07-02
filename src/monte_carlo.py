import numpy as np

import jbolo.utils as utils
import jbolo.jbolo_funcs as jf

class InputParam(object):
    """
    name : str
        name of parameter
    generate : function
        function takes n_sims and draws that many parameters for the time
    set_sim_param : function( sim, val)
        function takes a draw value and sets it in a sim configuration
    """
    def __init__(self, name, generate, set_sim_param):
        self.name = name
        self.generate = generate
        self.set_sim_param = set_sim_param

class InputParam_Psat(InputParam):
    """Detector Psats are special because, for most forecasting sims, these are set 
    by the optical loading on the detectors. Realitically, we use the central values
    to set our Psat detector requirements and then we 
    
    Arguments
    ----------
    name : str
        name of parameter
    base_sim_file : str
        file path to the base sim containing the central values for all the 
        input parameters
    error_frac : float
        the fractional error to set at the 1 sigma level for these parameters 
    """
    def __init__(self, name, base_sim_file, error_frac):
        self.name = name
        self.base_sim = base_sim_file
        self.error_frac = error_frac

    def generate(self, n_sims):
        sim = utils.load_sim(self.base_sim)
        jf.run_optics(sim)
        jf.run_bolos(sim)

        self.center_psats = {}
        for ch in sorted(sim['channels']):
            self.center_psats[ch] = sim['outputs'][ch]['P_sat']

        values = np.zeros( (n_sims, len(sim['channels'])) )

        for n, ch in enumerate(sorted(sim['channels'])):
            values[:,n] = np.random.normal( 
                loc=self.center_psats[ch], 
                scale=self.error_frac*self.center_psats[ch], 
                size=(n_sims,)
            )
        return values
        
    def set_sim_param(self, sim, val):
        sim['psat_method'] = 'specified'
        for n, ch in enumerate(sorted(sim['channels'])):
            sim['channels'][ch]['P_sat'] = val[n]
            
class OutputParam(object):
    """
    name : str
    by_channel : bool
    extract : function
        function takes a simulation (and channel if applicable) and returns
        the number to save
    """
    def __init__(self, name, extract, by_channel=True, dtype=np.float32):
        self.name = name
        self.extract = extract
        self.by_channel = by_channel
        self.dtype=dtype

    def setup(self, n_sims, channels):
        if not self.by_channel:
            return np.zeros( (n_sims,), dtype=self.dtype)
        out = {}
        for ch in channels:
            out[ch] = np.zeros( (n_sims,), dtype=self.dtype)
        return out
        
class SimulationMC(object):
    """
    name : str
    base_sim : str
        yaml file to base simulation off of
    input_params : list of InputParams
    output_params: list of OutputParams
    """
    def __init__(self, name, base_sim, inputs, outputs):
        self.name = name
        self.base_sim = base_sim
        sim = utils.load_sim(self.base_sim)
        self.channels = [ch for ch in sim['channels']]
        
        self.input_params = inputs
        self.output_params = outputs

        self.inputs = None
        self.outputs = None

    def setup(self, n_sims):
        self.n_sims = n_sims
        
        self.inputs = {}
        for in_param in self.input_params:
            self.inputs[in_param.name] = in_param.generate(n_sims)
        
        self.outputs = {}
        for param in self.output_params:
            self.outputs[param.name] = param.setup(n_sims, self.channels)

    def _set_params(self, sim, n):
        for param in self.input_params:
            param.set_sim_param( sim, self.inputs[param.name][n] )

    def _extract_params(self, sim, n):
        for param in self.output_params:
            if param.by_channel:
                for ch in self.channels:
                    self.outputs[param.name][ch][n] = param.extract( sim, ch)
            else:
                self.outputs[param.name][n] = param.extract(sim)
            
    def run(self):
        assert self.inputs is not None, "need to setup simulation first"

        for n in range(self.n_sims):
            sim = utils.load_sim(self.base_sim)
            self._set_params(sim, n)
            jf.run_optics(sim)
            jf.run_bolos(sim)
            self._extract_params( sim, n)