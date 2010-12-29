# -*- coding: utf-8 -*-

 #    This file is part of CasADi.
 #
 #    CasADi -- A symbolic framework for dynamic optimization.
 #    Copyright (C) 2010 by Joel Andersson, Moritz Diehl, K.U.Leuven. All rights reserved.
 #
 #    CasADi is free software; you can redistribute it and/or
 #    modify it under the terms of the GNU Lesser General Public
 #    License as published by the Free Software Foundation; either
 #    version 3 of the License, or (at your option) any later version.
 #
 #    CasADi is distributed in the hope that it will be useful,
 #    but WITHOUT ANY WARRANTY; without even the implied warranty of
 #    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 #    Lesser General Public License for more details.
 #
 #    You should have received a copy of the GNU Lesser General Public
 #    License along with CasADi; if not, write to the Free Software
 #    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

from casadi import *
from numpy import *
import matplotlib.pyplot as plt

# This demonstration is intended to demonstrate CasADi's Sundials interface
# The flags set in the beginning of the script demonstrates the most important features.
# Joel Andersson, 2010

# Use CVodes or IDAS
implicit_integrator = True

# test adjoint sensitivities
with_asens = True

# use exact jacobian
exact_jacobian = True

# Calculate the forward sensitivities using finite differences
finite_difference_fsens = not exact_jacobian

# Calculate initial condition (for IDAS only)
calc_ic = False

# Perturb x or u
perturb_u = True

# Use a user_defined linear solver
user_defined_solver = True

# Use sparse direct solver (SuperLU)
sparse_direct = True

# Second order sensitivities by a symbolic-numeric approach
second_order = True

# Create an IDAS instance (fully implicit integrator)
def create_IDAS():
  # Time 
  t = SX("t")

  # Differential states
  s = SX("s")
  v = SX("v")
  m = SX("m")
  y = [s,v,m]
  
  # State derivatives
  sdot = SX("sdot")
  vdot = SX("vdot")
  mdot = SX("mdot")
  ydot = [sdot,vdot,mdot]

  # Control
  u = SX("u")
  
  # Reference trajectory
  u_ref = 3-sin(t)
  
  # Square deviation from the state trajectory
  u_dev = u-u_ref
  u_dev *= u_dev
  
  # Differential equation (fully implicit form)
  res = [v - sdot,  (u-0.02*v*v)/m - vdot, -0.01*u*u - mdot]

  # Input of the DAE residual function
  ffcn_in = DAE_NUM_IN * [[]]
  ffcn_in[DAE_T] = [t]
  ffcn_in[DAE_Y] = y
  ffcn_in[DAE_YDOT] = ydot
  ffcn_in[DAE_P] = [u]

  # DAE residual function
  ffcn = SXFunction(ffcn_in,[res])
  ffcn.setOption("ad_order",1)
  
  # Quadrature function
  qfcn = SXFunction(ffcn_in,[[u_dev]])
  qfcn.setOption("ad_order",1)

  # Create an integrator
  integrator = IdasIntegrator(ffcn,qfcn)

  # Set IDAS specific options
  integrator.setOption("calc_ic",calc_ic)
  integrator.setOption("is_differential",[1,1,1])

  # Return the integrator
  return integrator

# Create an CVODES instance (ODE integrator)
def create_CVODES():
  # Time 
  t = SX("t")

  # Differential states
  s = SX("s")
  v = SX("v")
  m = SX("m")
  y = [s,v,m]
  
  # Control
  u = SX("u")
  
  # Reference trajectory
  u_ref = 3-sin(t)
  
  # Square deviation from the state trajectory
  u_dev = u-u_ref
  u_dev *= u_dev
  
  # Differential equation (fully implicit form)
  rhs = [v, (u-0.02*v*v)/m, -0.01*u*u]

  # Input of the DAE residual function
  ffcn_in = ODE_NUM_IN * [[]]
  ffcn_in[ODE_T] = [t]
  ffcn_in[ODE_Y] = y
  ffcn_in[ODE_P] = [u]

  # DAE residual function
  ffcn = SXFunction(ffcn_in,[rhs])
  ffcn.setOption("ad_order",1)
  
  # Quadrature function
  qfcn = SXFunction(ffcn_in,[[u_dev]])
  qfcn.setOption("ad_order",1)

  # Create an integrator
  integrator = CVodesIntegrator(ffcn,qfcn)
  
  # Return the integrator
  return integrator

# Time horizon
t0 = 0
tf = 10

# Bounds on the control
u_lb = -0.5
u_ub = 1.3
u_init = 1

# Initial conditions
y0 = [0,0,1]
  
# Full state including quadratures
x0 = list(y0)
x0.append(0)

# Integrator
if implicit_integrator:
  integrator = create_IDAS()
else:
  integrator = create_CVODES()

# Attach user-defined linear solver
if user_defined_solver:
  if sparse_direct:
    integrator.setLinearSolver(SuperLU(len(y0),len(y0)))
  else:
    integrator.setLinearSolver(LapackLUDense(len(y0),len(y0)))

# Set common integrator options
integrator.setOption("ad_order",1)
integrator.setOption("fsens_err_con",True)
integrator.setOption("quad_err_con",True)
integrator.setOption("abstol",1e-12)
integrator.setOption("reltol",1e-12)
integrator.setOption("fsens_abstol",1e-6)
integrator.setOption("fsens_reltol",1e-6)
integrator.setOption("asens_abstol",1e-6)
integrator.setOption("asens_reltol",1e-6)
integrator.setOption("exact_jacobian",exact_jacobian)
integrator.setOption("finite_difference_fsens",finite_difference_fsens)
integrator.setOption("max_num_steps",100000)
  
if(user_defined_solver):
  integrator.setOption("linear_solver","user_defined")

# Initialize the integrator
integrator.init()

# Set time horizon
integrator.setInput(t0,INTEGRATOR_T0)
integrator.setInput(tf,INTEGRATOR_TF)

# Set parameters
integrator.setInput(u_init,INTEGRATOR_P)

# Set inital state
integrator.setInput(x0,INTEGRATOR_X0)

# Set initial state derivative (if not to be calculated)
if not calc_ic:
  integrator.setInput([0,1,-0.01,0],INTEGRATOR_XP0)
  
# Integrate
integrator.evaluate()

# Save the result
res0 = integrator.getOutputData()

# Perturb in some direction
if perturb_u:
  u_pert = u_init + 0.01
  integrator.setInput(u_pert,INTEGRATOR_P)
else:
  x_pert = list(x0)
  x_pert[1] += 0.01
  integrator.setInput(x_pert,INTEGRATOR_X0)
  
# Integrate again
integrator.evaluate()
  
# Print statistics
integrator.printStats()

# Calculate finite difference approximation
fd = list(integrator.getOutputData())
for i in range(len(fd)):
  fd[i] -= res0[i]
  fd[i] /= 0.01
  
print "unperturbed                     ", res0
print "perturbed                       ", integrator.getOutputData()
print "finite_difference approximation ", fd

# forward seeds
if perturb_u:
  u_seed = 1
  integrator.setFwdSeed(u_seed,INTEGRATOR_P)
else:
  x0_seed = len(x0)*[0.]
  x0_seed[1] = 1
  print x0_seed
  integrator.setFwdSeed(x0_seed,INTEGRATOR_X0)
  
# Reset parameters
integrator.setInput(u_init,INTEGRATOR_P)
  
# Reset initial state
integrator.setInput(x0,INTEGRATOR_X0)

if with_asens:
  # backward seeds
  bseed = len(x0)*[0.]
  bseed[0] = 1
  integrator.setAdjSeed(bseed,INTEGRATOR_XF)

  # evaluate with forward and adjoint sensitivities
  integrator.evaluate(1,1)
else:
  # evaluate with only forward sensitivities
  integrator.evaluate(1,0)
    
print "forward sensitivities           ", integrator.getFwdSens()

if with_asens:
  print "adjoint sensitivities           ",
  print integrator.getAdjSens(INTEGRATOR_T0), " ",
  print integrator.getAdjSens(INTEGRATOR_TF), " ",
  print integrator.getAdjSens(INTEGRATOR_X0), " ",
  print integrator.getAdjSens(INTEGRATOR_P), " "
  
if second_order:
  # Generate the jacobian by creating a new integrator for the sensitivity equations by source transformation
  intjac = integrator.jacobian(INTEGRATOR_P,INTEGRATOR_XF)

  # Set options
  intjac.setOption("ad_order",1)
  intjac.setOption("number_of_fwd_dir",0)
  intjac.setOption("number_of_adj_dir",1)
    
  # Initialize the integrator
  intjac.init()

  # Set inputs
  intjac.setInput(t0,INTEGRATOR_T0)
  intjac.setInput(tf,INTEGRATOR_TF)
  intjac.setInput(u_init,INTEGRATOR_P)
  intjac.setInput(x0,INTEGRATOR_X0)
    
  # Set adjoint seed
  jacseed = 4*[0]
  jacseed[0] = 1;
  intjac.setAdjSeed(jacseed)
    
  # Evaluate the Jacobian
  intjac.evaluate(0,1)

  # Get the results
  print "second order (fwd-over-adj)     ",
  print intjac.getAdjSens(INTEGRATOR_X0), ", ",
  print intjac.getAdjSens(INTEGRATOR_P)

  
  
  
