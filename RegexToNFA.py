from manim import *

class LazyLine():
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def draw(self):
        line = Arrow(self.start.get_center(), self.end.get_center(),
                        tip_length=0.2, max_stroke_width_to_length_ratio=2)
        
        
        midpoint = (line.get_start() + line.get_end()) / 2
        label = Text('ε', font_size=12)
        
        if abs(self.start.get_center()[1] - self.end.get_center()[1]) < 0.1:
            label.next_to(line, UP, buff=0.05)
        else:
            label.move_to(line, midpoint + UP * 0.5)

        return (line, label)
    
class NFANode():
    def __init__(self, state, final):
        self.state = state 
        self.is_final = final
        self.edges = {}

    def add_edge(self, symbol, node):
        if symbol in self.edges:
            self.edges[symbol].append(node)
        else:
            self.edges[symbol] = [node]

    def add_one(self):
        visited = set()
        to_visit = [self]
        while len(to_visit) > 0:
            current = to_visit.pop()
            if current.state in visited:
                continue
            visited.add(current.state)
            current.state += 1  
            for _ , nodes in current.edges.items():
                for node in nodes:
                    to_visit.append(node)

class NFA():
    def __init__(self, start_node, end_node, vgroup, metdata):
        self.start_node = start_node
        self.end_node = end_node
        self.end_node.is_final = True
        self.vgroup = vgroup
        self.metadata = metdata

    def print_nfa(self):
        visited = set()
        to_visit = [self.start_node]

        while to_visit:
            current = to_visit.pop()
            if current.state in visited:
                continue
                    
            visited.add(current.state)
            for symbol, nodes in current.edges.items():
                for node in nodes:
                    print(f"State {current.state} {symbol} --> State {node.state}")
                    to_visit.insert(0, node)
            if current.is_final:
                print(f"State {current.state} is a final state.") 

class RegexParser():
    def __init__(self, regex):
        self.regex = regex
        self.position = 0
        self.state_nbr = 0
        self.metadata = {}

    def parse(self):
        start, end, vgroup = self._parse()
        if self.position != len(self.regex):
            raise ValueError(f"Unexpected character '{self.peek()}' at position {self.position}")
        end.is_final = True
        return NFA(start, end, vgroup, self.metadata)
    
    def _parse(self):
        return self.parse_union()

    def parse_union(self):
        start, end, vgroup_1 = self.parse_concat()
        
        first_or = True
        
        group_vgroup = VGroup()
        res_vgroup = VGroup()
        new_circle1 = Circle()
        new_circle2 = Circle()

        top_coord = vgroup_1.get_top()

        lines = []
        while self.peek() == '|':
            self.advance()
            next_start, next_end, vgroup_2 = self.parse_concat()

            if first_or:
                start, end = self.build_union_nfa(start, end, next_start, next_end)
                first_or = False

                new_circle1 = Circle(radius=0.3, color=BLACK)
                new_circle1.set_fill(WHITE, opacity=1)
                
                new_circle2 = Circle(radius=0.3, color=BLACK)
                new_circle2.set_fill(WHITE, opacity=1)


                group_vgroup.add(vgroup_1, vgroup_2)
                new_circle1.next_to(group_vgroup, LEFT, buff=0.3)
                new_circle2.next_to(group_vgroup, RIGHT, buff=0.3)               

                # new_circle1.shift(DOWN * 0.45)
                # new_circle2.shift(DOWN * 0.45)

                vgroup_2.next_to(vgroup_1, DOWN, buff=0.3)

                self.metadata[new_circle1] = start
                self.metadata[new_circle2] = end
                
                line_start1 = LazyLine(new_circle1, self.get_start(vgroup_1))                
                line_start2 = LazyLine(new_circle1, self.get_start(vgroup_2))
                line_end1 = LazyLine(self.get_end(vgroup_1), new_circle2)
                line_end2 = LazyLine(self.get_end(vgroup_2), new_circle2)

                lines = [line_start1, line_start2, line_end1, line_end2]

                bottom_coord = vgroup_2.get_bottom()
                midpoint_coord = (top_coord + bottom_coord) / 2
                new_circle1.move_to([new_circle1.get_center()[0], midpoint_coord[1], 0])
                new_circle2.move_to([new_circle2.get_center()[0], midpoint_coord[1], 0])

                res_vgroup.add(new_circle1, group_vgroup, new_circle2)
            
            else:
                start.add_edge('ε', next_start)
                next_end.add_edge('ε', end)

                vgroup_2.next_to(group_vgroup[-1], DOWN, buff=0.3)
                group_vgroup.add(vgroup_2)
        
                line_start = LazyLine(new_circle1, self.get_start(vgroup_2))
                line_end = LazyLine(self.get_end(vgroup_2), new_circle2)

                lines.append(line_start)
                lines.append(line_end)

                bottom_coord = vgroup_2.get_bottom()
                midpoint_coord = (top_coord + bottom_coord) / 2
                new_circle1.move_to([new_circle1.get_center()[0], midpoint_coord[1], 0])
                new_circle2.move_to([new_circle2.get_center()[0], midpoint_coord[1], 0])
                # res_vgroup =  VGroup(res_vgroup[:-1], line_start2, label_start2, line_end2, label_end2, res_vgroup[-1])

        if len(res_vgroup) == 0:
            return (start, end, vgroup_1)
        
        real_lines = self.from_virt_to_line(lines)
        elements = res_vgroup[:-1] + real_lines +  res_vgroup[-1]
        res_vgroup = VGroup(*elements)
        return (start, end, res_vgroup)
    
    def from_virt_to_line(self, lines):
        res = []
        for line in lines:
            l,label = line.draw()
            res.append(l)
            res.append(label)
        return res

    def parse_concat(self):
        start, end, vgroup = self.parse_star()

        while self.is_in_language(self.peek()):
            next_start, next_end, vgroup1 = self.parse_star()
            start, end, vgroup = self.build_concatenation_nfa(start, end, next_start, next_end, vgroup, vgroup1)

        return (start, end, vgroup)

    def parse_star(self):
        start,end,vgourp = self.parse_base()

        if self.peek() == '*':
            self.advance()
            start, end, vgourp = self.build_star_nfa(start,end, vgourp)
        
        return (start,end, vgourp)

    def parse_base(self):
        char = self.advance()

        if char == '(':
            node = self._parse()
            self.match(')')
            return node
        
        elif char.isdigit() or char.isalpha():
            node = self.build_singleton_nfa(char)
            return node
        
        
        raise ValueError(f"Unexpected character '{char}' at position {self.position}")

    def build_star_nfa(self, start, end, vgroup):
        
        new_start = NFANode(start.state, False)
        new_end = NFANode(0, False)
        
        start.add_one()
        new_end.state += end.state + 1

        new_start.add_edge('ε', start)
        new_start.add_edge('ε', new_end)
        
        end.add_edge('ε', new_end)
        end.add_edge('ε', start)

        self.state_nbr += 2

        new_circle1 = Circle(radius=0.3, color=BLACK)
        new_circle1.set_fill(WHITE, opacity=1)       

        vgroup.next_to(new_circle1, RIGHT, buff=0.3, aligned_edge=ORIGIN)
        new_circle2 = Circle(radius=0.3, color=BLACK)
        new_circle2.set_fill(WHITE, opacity=1)

        new_circle2.next_to(vgroup, RIGHT, buff=0.3, aligned_edge=ORIGIN)

        self.metadata[new_circle1] = new_start
        self.metadata[new_circle2] = new_end

        line1 = Arrow(new_circle1.get_center(), self.get_start(vgroup).get_center())
        label1 = Text('ε', font_size=12).next_to(line1, UP, buff=0.05)
        
        line2 = Arrow(self.get_end(vgroup).get_center(), new_circle2.get_center())
        label2 = Text('ε', font_size=12).next_to(line2, UP, buff=0.05)

        curve1 = CubicBezier(new_circle1.get_center() + 0.05, vgroup.get_center() + UP*1, 
                            new_circle2.get_left() + UP*1,new_circle2.get_center() + 0.05)

        midpoint1 = (new_circle1.get_center() + new_circle2.get_center() + 0.05) / 2 + UP*1

        curve_label1 = Text('ε', font_size=12).move_to(midpoint1)

        curve2 = CubicBezier(self.get_end(vgroup).get_center(), vgroup.get_center() + DOWN*1, 
                            new_circle1.get_right() + DOWN*1,new_circle1.get_center() - 0.05)

        midpoint2 = (vgroup[-1].get_center() + new_circle1.get_center() - 0.05) / 2 + DOWN*1

        curve_label2 = Text('ε', font_size=12).move_to(midpoint2)

        vgroup2 = VGroup(new_circle1, line1, line2, label1, label2, vgroup, curve1, curve_label1, curve2, curve_label2, new_circle2)

        return (new_start, new_end, vgroup2)

    def build_singleton_nfa(self, char):
        
        start_node = NFANode(self.state_nbr, False)
        self.state_nbr += 1
 
        final_node = NFANode(self.state_nbr, False)
        self.state_nbr += 1
        
        start_node.add_edge(char, final_node)

        circle1 = Circle(radius=0.3, color=BLACK)
        circle1.set_fill(WHITE, opacity=1)

        circle2 = Circle(radius=0.3, color=BLACK)
        circle2.set_fill(WHITE, opacity=1)
        circle2.next_to(circle1, RIGHT, buff=0.3)

        self.metadata[circle1] = start_node
        self.metadata[circle2] = final_node

        line = Arrow(circle1.get_center(), circle2.get_center())
        label = Text(char, font_size=12).next_to(line, UP, buff=0.05)

        vgroup = VGroup(circle1, line, label, circle2)
        
        return (start_node, final_node, vgroup)

    def build_concatenation_nfa(self, start1, end1, start2, end2, vgroup1, vgroup2):
        end1.add_edge('ε', start2)

        vgroup2.next_to(vgroup1, RIGHT, buff=0.3, aligned_edge=ORIGIN)
        line = Arrow(self.get_end(vgroup1).get_center(), self.get_start(vgroup2).get_center())
        label = Text('ε', font_size=12).next_to(line, UP, buff=0.05)

        vgroup = VGroup(vgroup1, line, label, vgroup2)
        return (start1, end2, vgroup)

    def get_end(self, vgroup):
        if isinstance(vgroup[-1], VGroup):
            return self.get_end(vgroup[-1])
        return vgroup[-1]

    def get_start(self, vgroup):
        if isinstance(vgroup[0], VGroup):
            return self.get_start(vgroup[0])
        return vgroup[0]

    def build_union_nfa(self, start1, end1, start2, end2):
        new_start = NFANode(start1.state, False)
        self.state_nbr += 1
        new_end = NFANode(self.state_nbr, False)
        self.state_nbr += 1

        start2.add_one()
        start1.add_one()

        new_start.add_edge('ε', start1)
        new_start.add_edge('ε', start2)

        end1.add_edge('ε', new_end)
        end2.add_edge('ε', new_end)

        return (new_start, new_end)

    def peek(self):
        if self.position < len(self.regex):
            return self.regex[self.position]
        return None

    def match(self, char):
        if self.position < len(self.regex) and self.regex[self.position] == char:
            self.position += 1
            return True
        raise ValueError(f"Expected '{char}' at position {self.position}")

    def advance(self):
        if self.position < len(self.regex):
            self.position += 1
            return self.regex[self.position-1]
        
        return None

    def is_in_language(self, char):
        if char is None:
            return False
        return char.isdigit() or char.isalpha() or char == '('

regex = input("Regular Expression allowed symbols (*, | , (, ), a...b , 0...9) (no space) : ")
class MainClass(Scene):
    def construct(self):
        # regex = "a|b"
        parser = RegexParser(regex)
        nfa = parser.parse()
        nfa.vgroup.move_to(ORIGIN)
        textg = Text(f"Regex: {regex}", font_size=24).to_edge(UP)
        self.play(Write(textg))
        self._visualize(nfa.vgroup, nfa.metadata)

        # nfa.print_nfa()
        self.wait(2)
    def _visualize(self, vgroup, metadata): 
        for mobject in vgroup:
            if isinstance(mobject, VGroup):
                self._visualize(mobject, metadata)
            elif isinstance(mobject, Circle):
                text = Text("s" + str(metadata[mobject].state), font_size=12 ,color=BLACK)
                text.move_to(mobject.get_center())
                self.play(Create(mobject))
                self.play(Write(text))
            elif isinstance(mobject, Text):
                self.play(Write(mobject))
            elif isinstance(mobject, Arrow) or isinstance(mobject, CubicBezier):
                self.play(Create(mobject))
