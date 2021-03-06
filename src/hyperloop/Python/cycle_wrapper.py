# File wrapping NPSS Hyperloop Model.

import sys
import os
import traceback
from math import pi
import numpy as np
from collections import OrderedDict

from six import iteritems, iterkeys

from openmdao.api import Problem, Group, ExternalCode

# fpath = os.path.dirname(os.path.realpath(__file__))
# ref_data = np.loadtxt(fpath + '/cycle.csv',
#                       delimiter=',', skiprows=1)
# # headers to extract from csv file


# header = ['inlet.eRamBase','fan.PR','fan.eff','comp.PR','comp.eff','burn.FAR','burn.eff',
#         'turbL.eff','turbL.PR','turbH.eff','turbH.PR','nozz_byp.Cfg','nozz_core.Cfg',
#         'shaftL.Nmech','shaftH.Nmech','amb.MN','amb.alt','start.W','start.Pt','start.Tt',
#         'start.Fl_O.ht','start.Fl_O.s','start.Fl_O.MN','start.Fl_O.V','start.Fl_O.A',
#         'inlet.Fl_O.W','inlet.Fl_O.Pt','inlet.Fl_O.Tt','inlet.Fl_O.ht','inlet.Fl_O.s',
#         'inlet.Fl_O.MN','inlet.Fram','inlet.Fl_O.V','inlet.Fl_O.A','fan.Fl_O.W','fan.Fl_O.Pt',
#         'fan.Fl_O.Tt','fan.Fl_O.ht','fan.Fl_O.s','fan.Fl_O.MN','fan.Fl_O.V',
#         'fan.Fl_O.A','comp.Fl_O.W','comp.Fl_O.Pt','comp.Fl_O.Tt','comp.Fl_O.ht',
#         'comp.Fl_O.s','comp.Fl_O.MN','comp.Fl_O.V','comp.Fl_O.A','burn.Fl_O.W',
#         'burn.Fl_O.Pt','burn.Fl_O.Tt','burn.Fl_O.ht','burn.Fl_O.s','burn.Fl_O.MN',
#         'burn.Fl_O.V','burn.Fl_O.A','turbL.Fl_O.W','turbL.Fl_O.Pt','turbL.Fl_O.Tt',
#         'turbL.Fl_O.ht','turbL.Fl_O.s','turbL.Fl_O.MN','turbL.Fl_O.V','turbL.Fl_O.A',
#         'turbH.Fl_O.W','turbH.Fl_O.Pt','turbH.Fl_O.Tt','turbH.Fl_O.ht','turbH.Fl_O.s',
#         'turbH.Fl_O.MN','turbH.Fl_O.V','turbH.Fl_O.A','nozz_byp.Fl_O.W','nozz_byp.Fl_O.Pt',
#         'nozz_byp.Fl_O.Tt','nozz_byp.Fl_O.ht','nozz_byp.Fl_O.s','nozz_byp.Fl_O.MN',
#         'nozz_byp.PsExh','nozz_byp.Fg','nozz_byp.Fl_O.V','nozz_byp.Fl_O.A','nozz_core.Fl_O.W',
#         'nozz_core.Fl_O.Pt','nozz_core.Fl_O.Tt','nozz_core.Fl_O.ht','nozz_core.Fl_O.s',
#         'nozz_core.Fl_O.MN','nozz_core.PsExh','nozz_core.Fg','nozz_core.Fl_O.V','nozz_core.Fl_O.A',
#         'shaftH.trqIn','shaftH.trqOut','shaftH.trqNet','shaftH.pwrIn','shaftH.pwrOut',
#         'shaftH.pwrNet','shaftL.trqIn','shaftL.trqOut','shaftL.trqNet','shaftL.pwrIn',
#         'shaftL.pwrOut','shaftL.pwrNet','perf.SFC','perf.Fn']
# h_map = dict(((v_name, i) for i, v_name in enumerate(header)))

# data = ref_data[2]


class CycleWrap(ExternalCode):

    num_calls = 0

    def __init__(self):
        super(CycleWrap, self).__init__()

        # inputs
        self.initparam = OrderedDict()
        self.initparam['vehicleMach'] = 0.8
        self.initparam['cmpMach'] = 0.65
        self.initparam['PsTube'] = 0.5
        self.initparam['TsTube'] = 524.0
        self.initparam['Apod'] = 0.9
        self.initparam['Abypass'] = 0.9
        self.initparam['blockage'] = 0.9
        self.initparam['start.W'] = 10.
        self.initparam['split.BPR'] = 0.5
        self.initparam['inlet.PqP_in'] = 0.99
        self.initparam['cmp25.PRdes'] = 12.5
        self.initparam['cmp25.effDes'] = 0.9
        self.initparam['shaft.Nmech'] = 10000.
        self.initparam['bypass.Fl_O.MN'] = 0.95
        self.initparam['bypassExit.Fl_O.MN'] = 0.5
        self.initparam['nozz.PsExhName'] = 'bypassExit.Fl_O.Ps'
        self.initparam['nozz.switchType'] = 'CON_DIV'

        #constraints (dependents)
        self.initparam['dep_Wcmp.eq_lhs'] = '3000.0' #cmp25.pwr
        self.initparam['dep_Apod.eq_lhs'] = '1.4' #Apax

        for varname, val in iteritems(self.initparam):
            name = varname.replace('.', ':')
            self.add_param(name, val)

        # Unknowns
        self.initunknown = OrderedDict()
        self.initunknown['converged'] = 0.0
        #self.initunknown['elapsedTime'] = 0.0
        #self.initunknown['PNT3m_beta'] = np.zeros(10)
        self.initunknown['nozz.Fg'] = 0.0
        # self.initunknown['AtubeB'] = 0.0
        # self.initunknown['AtubeC'] = 0.0
        #self.initunknown['Abypass'] = 0.0
        # self.initunknown['Apod'] = 0.0
        # self.initunknown['Adiff'] = 0.0
        # self.initunknown['Acmprssd'] = 0.0
        # self.initunknown['Apax'] = 0.0
        # self.initunknown['turbH.eff'] = 0.0
        # self.initunknown['turbH.PR'] = 0.0
        # self.initunknown['nozz_byp.Cfg'] = 0.0
        # self.initunknown['nozz_core.Cfg'] = 0.0
        #self.initunknown['shaftL.Nmech'] = 0.0
        #self.initunknown['shaftH.Nmech'] = 0.0

        for varname, val in iteritems(self.initunknown):
            name = varname.replace('.', ':')
            self.add_output(name, val=val)

        self.add_output('success', val=1.0)

        # Run filenames dependent on OS
        mydir = os.path.dirname(os.path.abspath(__file__))
        if sys.platform.startswith('win'):
            cmdfile = os.path.join(mydir, 'run_npss.bat')
        else:
            cmdfile = os.path.join(mydir, 'run_npss.sh')

        self.options['command'] = ['runnpss','../NPSS/magneplane.mdl'] #[cmdfile, os.path.join(mydir, 'cycle_NPSS.mdl')]
        self.options['timeout'] = 300.0  # 600.0
        #self.options['on_timeout'] = 'continue'
        #self.options['on_error'] = 'continue'

    def _setup_communicators(self, comm, pdir):
        super(CycleWrap, self)._setup_communicators(comm, pdir)
        self.npss_input = 'design_inputs.int' # generated by wrapper, used as NPSS input
        self.npss_output = '../NPSS/wrapper.out' # output of NPSS, read back into wrapper
        # with self._dircontext:
        #     if not os.path.exists('Output'):
        #         os.makedirs('Output')
        #     if os.path.exists(self.npss_output):
        #         os.remove(self.npss_output)

    def solve_nonlinear(self, params, unknowns, resids):
        """ Executes our file-wrapped component. """

        self.load_inputs(params, unknowns, resids)

        #parent solve_nonlinear function actually runs the external code
        super(CycleWrap, self).solve_nonlinear(params, unknowns, resids)

        self.parse_outputs(params, unknowns, resids)
        self.num_calls += 1


    def load_inputs(self, params, unknowns, resids):
        """ Prepares NPSS input file with our openmdao values. """

        with open(self.npss_input, 'w') as f:
            for varname in iterkeys(self.initparam):
                ourname = varname.replace('.', ':')
                val = params[ourname]

                if type(val) is str:
                    f.write('%s = "%s";\n' % (varname, val))
                else:
                    f.write('%s = %.15f;\n' % (varname, val))

    def parse_outputs(self, params, unknowns, resids):
        """ Reads outputs from NPSS and puts them into our unknowns. """
        try:
            with open(self.npss_output, 'r') as f:
                i = 0;
                for line, var_name in zip(f, self.initunknown.keys()):
                    if i==0: # first line is csv header
                        l = line.rstrip('\r\n')
                        names = l.split(',')
                        i=1
                    else: # second line is the output
                        l = line.rstrip('\r\n')
                        values = l.split(',')

                        for name, val in zip(names,values):
                            #print (name,val)
                            try:
                                unknowns[name.replace('.', ':')] = float(val)
                            except KeyError:
                                pass
                    # name = var_name.replace('.', ':')
                    # data = line.split("=")[1].strip()
                    # if data[0] == "{":
                    #     data = np.array([float(x) for x in data[1:-1].split(',')])
                    # else:
                    #     data = float(data)
                    # unknowns[name] = data
            #os.remove(self.npss_output)
            #print(dictionary)
            #print(unknowns['inlet:eRamBase'])
            unknowns['success'] = 1.0
            # print(10*"=")
            # print("BPR", params['split:BPRdes'])
            # print("fan PR", params['fan:PRdes'])
            # print("comp PR", params['compressor:PRdes'])
            # print("W", params['start:W_in'])
            # print("alt", params['amb:alt_in'])
            # print("t4", unknowns['burn:Fl_O:Tt'])
            # print("fn", unknowns['perf:Fn'])
            # print("OPR", unknowns['perf:myOPR'])
            # print("SFC", unknowns['perf:SFC'])
            #sys.stdout.flush()
        except:
            print(traceback.format_exc())
            unknowns.vec[:] = 0.0
            try:
                pass
                #os.remove(self.npss_output)
            except:
                pass


if __name__ == "__main__":

    from openmdao.api import IndepVarComp

    top = Problem()
    root = top.root = Group()

    root.add('cycle', CycleWrap())

    # params = (
    #     ('vehicleMach', 0.8),
    #     ('cmpMach', 0.65),
    #     ('PsTube', 0.5),
    #     ('TsTube', 524.0),
    #     ('Apod', 0.9),
    #     ('Abypass', 0.9),
    #     ('blockage', 0.9 ),
    #     ('start:W', 10.),
    #     ('split:BPR', 0.5),
    #     ('inlet:PqP_in', 0.99),
    #     ('cmp25:PRdes', 12.5),
    #     ('cmp25:effDes', 0.9),
    #     ('shaft:Nmech', 10000.),
    #     ('bypass.Fl_O.MN', 0.95),
    #     ('bypassExit.Fl_O.MN', 0.5),
    # )

    # top.root.add('des_vars', IndepVarComp(params))

    # top.root.connect('des_vars.vehicleMach', 'cycle.vehicleMach')
    # top.root.connect('des_vars.cmpMach', 'cycle.cmpMach')
    # top.root.connect('des_vars.PsTube', 'cycle.PsTube'
    # top.root.connect('des_vars.TsTube', 'cycle.TsTube')
    # top.root.connect('des_vars.Apod', 'cycle.Apod')
    # top.root.connect('des_vars.Abypass', 'cycle.Abypass')
    # top.root.connect('des_vars.blockage', 'cycle.blockage' )
    # top.root.connect('des_vars.start:W', 'cycle.start:W')
    # top.root.connect('des_vars.split:BPR', 'cycle.split:BPR')
    # top.root.connect('des_vars.inlet:PqP_in', 'cycle.inlet:PqP_in')
    # top.root.connect('des_vars.cmp25:PRdes', 'cycle.cmp25:PRdes')
    # top.root.connect('des_vars.cmp25:effDes', 'cycle.cmp25:effDes')
    # top.root.connect('des_vars.shaft:Nmech', 'cycle.shaft:Nmech')
    # top.root.connect('des_vars.bypass.Fl_O.MN', 'cycle.bypass.Fl_O.MN')
    # top.root.connect('des_vars.bypassExit.Fl_O.MN', 'cycle.bypassExit.Fl_O.MN')

    # top.root.fd_options['force_fd'] = True
    # top.root.fd_options['step_size'] = 1e-4
    # top.root.fd_options['form'] = 'central'

    # from openmdao.drivers.pyoptsparse_driver import pyOptSparseDriver
    # top.driver = pyOptSparseDriver()
    # top.driver.options['optimizer'] = "SNOPT"
    # top.driver.options['print_results'] = False
    # #top.driver.options['gradient method'] = "snopt_fd"
    # top.driver.opt_settings = {'Major optimality tolerance': 1e-3,
    #                              'Major feasibility tolerance': 1.0e-5,
    #                              'Iterations limit': 500000000}


    # # configure design variables
    # top.driver.add_desvar('des_vars.split:BPR', lower=2.0, upper=12.0, scaler=1.0)
    # top.driver.add_desvar('des_vars.cmp25:PR', lower=1.0, upper=30.0, scaler=1.0)
    # top.driver.add_desvar('des_vars.start:W', lower=1.0, upper=2000.0, scaler=1.0)

    # # add our objective
    # top.driver.add_objective('cycle.Atube')

    # top.driver.add_constraint('cycle.cmp25.pwr', equals=3000.0)
    # top.driver.add_constraint('cycle.Apax', equals=1.4)

    # from openmdao.recorders.sqlite_recorder import SqliteRecorder
    # rec = SqliteRecorder(out='data.sql')
    # top.driver.add_recorder(rec)
    # rec.options['record_derivs'] = False

    top.setup(check=True)


    # top['des_vars.start:W']   = data[h_map['start.W']]
    # top['des_vars.amb:MN_in']  = data[h_map['amb.MN']]
    # top['des_vars.cmp25:PRdes'] = data[h_map['cmp25.PR']]

    # top['cycle.inlet:eRamBase'] = data[h_map['inlet.eRamBase']]
    # top['cycle.cmp25:effDes'] = data[h_map['cmp25.eff']]
    # top['cycle.nozz_core:Cfg'] = data[h_map['nozz_core.Cfg']]
    # top['cycle.nozz_byp:Cfg'] = data[h_map['nozz_byp.Cfg']]
    # top['cycle.shaft:Nmech'] = data[h_map['shaftL.Nmech']]
    import time

    t = time.time()
    top.run()

    print("time", (time.time() - t))

    # print("num_calls:", top.root.cycle.num_calls)
    #print("success", top['turboF.success'])
    print
    print
    print("Fg", top['cycle.nozz:Fg'])

    # inputs = ['des_vars.split:BPR', 'des_vars.comp25:PRdes',
    #           'des_vars.vehicleMach', 'des_vars.cmpMach']
    # outputs = ['cycle.AtubeB', 'cycle.AtubeC', 'cycle.Atube']

    # print top.calc_gradient(inputs, outputs)
