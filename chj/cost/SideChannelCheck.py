# ------------------------------------------------------------------------------
# CodeHawk Java Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2016-2020 Kestrel Technology LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ------------------------------------------------------------------------------

from chj.cost.CostMeasure import CostMeasure

class SideChannelCheck:

    def __init__(self,jmc,xnode):
        self.mc = mc                        # MethodCost               
        self.costmodel = self.mc.costmodel
        self.xnode = xnode
        self.paths = {}             # pred-pc -> CostMeasure
        self.decisionpc = int(self.xnode.get('decision-pc'))
        self.observationpc = int(self.xnode.get('observation-pc')) 

    def get_method(self): return self.jmc.get_method()

    def get_paths(self):
        return self.path.values()

    def get_full_paths(self):
        cfg = self.get_method().get_cfg()
        return cfg.enumerate_paths(self.decisionpc,self.observationpc)

    def get_full_paths_through_pc(self,pc):
        fullpaths = self.get_full_paths()
        return [ x for x in fullpaths if x[-2] == pc ]

    def get_longest_full_paths_through_pc(self,pc):
        fullpaths = self.get_full_paths_through_pc(pc)
        sets = set([])
        for p in fullpaths:
            sets.add(frozenset(p))
        maximalsets = set([])
        for s in sets:
            if any(x for x in sets if s != x and s.issubset(x)): continue
            maximalsets.add(s)
        maximalpaths = []
        for p in fullpaths:
            if set(p) in maximalsets:
                maximalpaths.append(p)
        return maximalpaths

    def get_conditions_in_path(self,p):
        result = []
        m = self.get_method()
        cfg = self.get_method().get_cfg()
        cfg = self.get_method().get_cfg()
        for (n,e) in enumerate(p) :
            b = cfg.get_block(e)
            if b.has_conditions() and n < len(p) - 1:
                if m.is_loop_head(e) and e in p[n+1:]:
                    bound = m.get_loop(e).get_bound()
                    result.append((str(e),'L:' + b.get_fcond() + ' (bound: ' + str(bound) + ')'))
                elif p[n+1] == m.get_next_pc(b.lastpc):
                    result.append((str(e),b.get_fcond()))
                else:
                    result.append((str(e),b.get_tcond()))
        return result

    def __str__(self):
        lines = []
        cfg = self.get_method().get_cfg()
        lines.append('decision-pc   : ' + str(self.decisionpc))
        lines.append('observation-pc: ' + str(self.observationpc))
        decisionblock = self.jmc.get_method().get_cfg().get_block(self.decisionpc)
        
        if decisionblock.has_conditions():
            tcond = decisionblock.get_tcond()
            fcond = decisionblock.get_fcond()
            lines.append('conditions at decision-pc: ')
            lines.append('  T: ' + str(tcond))
            lines.append('  F: ' + str(fcond))
        else:
            lines.append('No conditions found decision-pc')
        lines.append(' ')

        fullpaths = cfg.enumerate_paths(self.decisionpc,self.observationpc)
                             
        lines.append('  path through pc=        cost')
        lines.append('-' * 80)
        for p in sorted(fullpaths):
            lbblockcosts = [ self.jmc.get_block_cost(pc).cost.get_lower_bounds().get_jterms()[0] for pc in p ]
            ubblockcosts = [ self.jmc.get_block_cost(pc).cost.get_upper_bounds().get_jterms()[0] for pc in p ]
            lbcost = lbblockcosts[0]
            ubcost = ubblockcosts[0]
            for c in lbblockcosts:
                lbcost = lbcost.add(c).simplify()
            for c in ubblockcosts:
                ubcost = ubcost.add(c).simplify()
            lines.append('  ' + str(p).rjust(45) + ': [' + str(lbcost).rjust(20) + ' ; ' + str(ubcost).rjust(20) + ']')

        lines.append(' ')
        for p in sorted(self.paths):
            lines.append('Paths through ' + str(p))
            pathsthroughp = self.get_longest_full_paths_through_pc(p)
            for pp in pathsthroughp:
                lines.append('  ' + str(pp))
                conds = self.get_conditions_in_path(pp[1:])
                for (pc,c) in conds:
                    lines.append('    ' + str(pc) + ': ' + str(c))
                    
        return '\n'.join(lines)

