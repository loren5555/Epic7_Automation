class HsvFilter:
    def __init__(self, h_min=None, h_max=None, s_min=None, s_max=None, v_min=None, v_max=None,
                 s_sub=None, v_sub=None, s_add=None, v_add=None):
        self.h_min = h_min
        self.h_max = h_max
        self.s_min = s_min
        self.s_max = s_max
        self.v_min = v_min
        self.v_max = v_max
        self.s_sub = s_sub
        self.v_sub = v_sub
        self.s_add = s_add
        self.v_add = v_add
