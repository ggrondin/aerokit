
"""
    The ``nozzle`` module
    =========================
 
    Provides specific functions for computation of 1D defintion of nozzles via section law
 
    :Example:
 
    >>> import aerokit.aero.nozzle as nz
 
    Available functions
    -------------------
 
	.. note:: Specific heat ratio `gamma` is defined only using aerokit.common.defaultgas module
"""

import numpy as np
from aerokit.common import defaultgas as defg # relative import is deprecated by doctest
from aerokit.aero   import Isentropic as Is
from aerokit.aero   import MassFlow   as mf
from aerokit.aero   import ShockWave  as sw

# === NPR computation from As/Ac definition of nozzle ===

def NPR_choked_subsonic(AsAc):
	"""Compute Nozzle Pressure Ratio to get a choked but subsonic regime in a nozzle with As/Ac diffuser

	Args:
		AsAc ([real]): ratio of exit over throat surfaces 
	Returns:
		[real]: Nozzle Pressure ratio (inlet total pressure over exit static pressure)
	"""
	return Is.PtPs_Mach(mf.MachSub_Sigma(AsAc))

def NPR_choked_supersonic(AsAc):
	"""Compute Nozzle Pressure Ratio to get a choked supersonic regime in a nozzle with As/Ac diffuser

	Args:
		AsAc ([real]): ratio of exit over throat surfaces 
	Returns:
		[real]: Nozzle Pressure ratio (inlet total pressure over exit static pressure)
	"""
	return Is.PtPs_Mach(mf.MachSup_Sigma(AsAc))

def NPR_shock_at_exit(AsAc):
	"""Compute Nozzle Pressure Ratio to get a choked, supersonic regime but shock at exit in a nozzle with As/Ac diffuser

	Args:
		AsAc ([real]): ratio of exit over throat surfaces 
	Returns:
		[real]: Nozzle Pressure ratio (inlet total pressure over exit static pressure)
	"""
	Msup  = mf.MachSup_Sigma(AsAc)
	Msh   = sw.downstream_Mn(Msup)
	return Is.PtPs_Mach(Msh) / sw.Pi_ratio(Msup)

def _NPR_Ms_list(AsAc):
	"""
    	Computes all NPR limits and associated exit Mach number

		internal function
 
		:param AsAc:  ratio of section at exit over throat
		:return:      result NPR and Mach numbers
 
 		:Example:

		>>> import aerokit.aero.MassFlow as mf ; mf.Sigma_Mach(Is.Mach_PtPs(np.array(_NPR_Ms_list(2.)[:3:2])))
		array([ 2.,  2.])

		.. seealso:: NPR_choked_subsonic(), NPR_choked_supersonic(), NPR_shock_at_exit()
		.. note:: available for scalar or array (numpy) computations
    """
	Msub  = mf.MachSub_Sigma(AsAc)
	NPR0  = Is.PtPs_Mach(Msub)
	Msup  = mf.MachSup_Sigma(AsAc)
	Msh   = sw.downstream_Mn(Msup)
	NPRsw = Is.PtPs_Mach(Msh) / sw.Pi_ratio(Msup)
	NPR1  = Is.PtPs_Mach(Msup)
	return NPR0, NPRsw, NPR1, Msub, Msh, Msup

def Ms_from_AsAc_NPR(AsAc, NPR):
	"""
    	Computes Mach number at exit of a nozzle given As/Ac and NPR

		This method checks the NPR to define regime and computes Mach number at exit
 
		:param AsAc:  ratio of section at exit over throat
        :param NPR:   ratio of total pressure at inlet over 'expected' static pressure at exit
		:return:      result Mach number at exit
 
 		:Example:

		>>> print round(Ms_from_AsAc_NPR(2.636, 1.5), 8) # case with shock in diffuser
		0.32586574

		.. seealso:: 
		.. note:: NOT available for array (numpy) computations
    """	
	NPR0, NPRsw, NPR1, Msub, Msh, Msup = _NPR_Ms_list(AsAc)
	if (NPR < NPR0):
		Ms = Is.Mach_PtPs(NPR)
	elif (NPR > NPRsw): 
		Ms = Msup
	else:
		gmu = defg._gamma-1.
		K   = NPR/AsAc/((defg._gamma+1.)/2)**((defg._gamma+1.)/2/gmu)
		Ms  = np.sqrt((np.sqrt(1.+2.*gmu*K*K)-1.)/gmu)
	return Ms

def Madapt_from_AsAc_NPR(AsAc, NPR):
	"""
    	Computes Mach number for pressure adapted flow of a nozzle given As/Ac and NPR

		This method checks the NPR to define regime and computes Mach number in jet. The switch between 
		overexpanded jet and underexpanded jet is 
 
		:param AsAc:  ratio of section at exit over throat
        :param NPR:   ratio of total pressure at inlet over 'expected' static pressure at exit
		:return:      result Mach number at exit
 
 		:Example:

		>>> print round(Ms_from_AsAc_NPR(2.636, 1.5), 8) # case with shock in diffuser
		0.32586574

		.. seealso:: 
		.. note:: NOT available for array (numpy) computations
    """	
	NPR0, NPRsw, NPR1, Msub, Msh, Msup = _NPR_Ms_list(AsAc)
	if (NPR < NPR0):
		Ms = Is.Mach_PtPs(NPR)
	elif (NPR > NPR1): # under expanded flow
		Ms = Is.Mach_PtPs(NPR)
	elif (NPR > NPRsw): # shock wave in jet
		Ms = sw.downstreamMach_Mach_ShockPsratio(Msup, NPR1/NPR)
	else:
		gmu = defg._gamma-1.
		K   = NPR/AsAc/((defg._gamma+1.)/2)**((defg._gamma+1.)/2/gmu)
		Ms  = np.sqrt((np.sqrt(1.+2.*gmu*K*K)-1.)/gmu)
	return Ms

class nozzle():
	""" Define a nozzle

	:param x: coordinate for section, not really used for now
	:param section: array of section law
	:param AsoAc: force AsoAc instead of computing from section law
	:param gamma: ratio of specific heats
	:param NPR: NPR value (>1); if None (default), can be set with nozzle.set_NPR(NPR)
	:param ref_rttot: additional definition of r*Ttot to complete state (default 1.)
	:param scale_ps: arbitrary scaling of static (and associated total) pressure (default 1. at the outlet)
	"""

	def __init__(self, x, section, AsoAc=None, gamma=1.4, NPR=None, ref_rttot=1., scale_ps=1.):

		self.gamma   = gamma
		self.x       = x
		if AsoAc:
			self.AsoAc = AsoAc
		else:
			self.AsoAc = section[-1] / np.min(section)
		self.AxoAc   = section * self.AsoAc / section[-1]
		self.ithroat = np.abs(self.AxoAc).argmin() # abs not necessary but ensure conversion to numpy array
		defg.save_default()
		self.NPR0, self.NPRsw, self.NPR1, self.Msub, self.Msh, self.Msup = _NPR_Ms_list(self.AsoAc)
		self._ref_rttot = ref_rttot
		self._scale_ps  = scale_ps
		if NPR:
			self.set_NPR(NPR)
		defg.restore_default()
		return

	def set_NPR(self, NPR):
		""" Define Nozzle Pressure Ratio (inlet Ptot over outlet Ps) for this case
		Define Nozzle pressure ratio and compute Mach number, Ptot and Ps according to nozzle regime
        :param NPR: NPR value (>1)

		"""
		self._Pt = np.ones_like(self.AxoAc)
		if NPR < self.NPR0:
			_Ms = Is.Mach_PtPs(NPR, gamma=self.gamma)
			self._M  = mf.MachSub_Sigma(self.AxoAc/self.AsoAc*mf.Sigma_Mach(_Ms), gamma=self.gamma)
			self._Ps = self._Pt/Is.PtPs_Mach(self._M, gamma=self.gamma)
		else:
			self._M = np.ones_like(self.AxoAc)
			self._M[:self.ithroat+1]   = mf.MachSub_Sigma(self.AxoAc[:self.ithroat+1],   gamma=self.gamma)
			self._M[self.ithroat+1:] = mf.MachSup_Sigma(self.AxoAc[self.ithroat+1:], gamma=self.gamma)
			if NPR < self.NPRsw:
				# analytical solution for Ms, losses and upstream Mach number of shock wave
				Ms     = Ms_from_AsAc_NPR(self.AsoAc, NPR)
				Ptloss = Is.PtPs_Mach(Ms)/NPR
				Msh    = sw.Mn_Pi_ratio(Ptloss)
				# redefine curves starting from 'ish' index (closest value of Msh in supersonic flow)
				ish    = np.abs(self._M-Msh).argmin()
				self._M[ish:] = mf.MachSub_Sigma(self.AxoAc[ish:]*mf.Sigma_Mach(Ms)/self.AsoAc)
				self._Pt[ish:] = Ptloss
			self._Ps = self._Pt/Is.PtPs_Mach(self._M)


	def Mach(self):
		return self._M

	def Ps(self):
		return self._Ps

	def Ptot(self):
		return self._Pt


# ===============================================================
# automatic testing

if __name__ == "__main__":
    import doctest
    doctest.testmod()