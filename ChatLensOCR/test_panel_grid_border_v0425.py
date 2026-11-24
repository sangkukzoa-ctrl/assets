import unittest
from panel_grid_v0423 import _remove_border_pipe
class BorderTests(unittest.TestCase):
    def test_right_full_height(self):
        self.assertEqual(_remove_border_pipe('Apply |',[{'text':'|','box':(95,0,100,40)}],(100,40)),('Apply',[]))
    def test_left_full_height(self):
        self.assertEqual(_remove_border_pipe('| Apply',[{'text':'|','box':(0,0,2,40)}],(100,40)),('Apply',[]))
    def test_interior_literal(self):
        items=[{'text':'|','box':(70,5,73,35)}]
        self.assertEqual(_remove_border_pipe('Apply |',items,(100,40)),('Apply |',items))
    def test_standalone_literal(self):
        items=[{'text':'|','box':(95,0,100,40)}]
        self.assertEqual(_remove_border_pipe('|',items,(100,40)),('|',items))
    def test_embedded_literal(self):
        items=[{'text':'|','box':(95,0,100,40)}]
        self.assertEqual(_remove_border_pipe('|A|',items,(100,40)),('|A|',items))
    def test_no_geometry(self):
        self.assertEqual(_remove_border_pipe('Apply |',[],(100,40)),('Apply |',[]))
if __name__=='__main__': unittest.main()
