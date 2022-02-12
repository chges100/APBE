import numpy as np

import kivy
kivy.require('1.10.0')
  
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.uix.scatter import ScatterPlane
from kivy.uix.scatter import Scatter
from kivy.uix.recycleview import RecycleView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stencilview import StencilView
from kivy.uix.button import Button
from kivy.lang import Builder
from scipy.interpolate import interp2d

from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

import cv2

Builder.load_string('''
<PointListView>:
    viewclass: 'Label'
    RecycleBoxLayout:
        default_size: None, dp(56)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'
''')


class PointListView(RecycleView):
    def __init__(self, point_list, **kwargs):
        super(PointListView, self).__init__(**kwargs)
        self.data = [({'text': str(point)}) for point in point_list]
        print(self.data)
        self.viewclass = 'Label'

    def update_data(self, point_list):
        self.data = [({'text': str(point)}) for point in point_list]

class ImageView(StencilView):
    def __init__(self, **kwargs):
        super(ImageView, self).__init__(**kwargs)
        
        self.sp = ScatterPlane()
        self.sp.do_translation=True

        self.add_widget(self.sp)

    def set_image(self, img):
        self.img = img
        
        w, h, _ = self.img.shape
        self.texture = Texture.create(size=(h,w))
        self.texture.blit_buffer(self.img.flatten(), colorfmt='rgb', bufferfmt='float')

        with self.sp.canvas:
            Rectangle(texture = self.texture, pos=self.pos, size=(h,w))

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            if touch.is_mouse_scrolling:
                if touch.button == 'scrolldown':
                    if self.sp.scale < 10:
                        self.sp.scale = self.sp.scale * 1.1
                elif touch.button == 'scrollup':
                    #if self.sp.scale > 1:
                    self.sp.scale = self.sp.scale * 0.8
            elif touch.button == 'left':
                super(ImageView, self).on_touch_down(touch)

class ImageViewClickable(ImageView):
    def __init__(self, point_list, **kwargs):
        super(ImageViewClickable, self).__init__(**kwargs)
        self.point_list = point_list

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            if touch.button == 'right':
                with self.sp.canvas:
                    if self.sp.collide_point(touch.x, touch.y):
                        loc_x, loc_y = self.sp.to_local(touch.x, touch.y)
                        Color(1,0,0)
                        l = 24
                        Rectangle(pos=(loc_x - l/2, loc_y - l/2), size=(l,l))
                        Color(1,1,1)
                        self.point_list.append((loc_x, loc_y))
                        print(self.point_list)

            super(ImageViewClickable, self).on_touch_down(touch)

class MyLayout(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.sample_radius=8

        self.point_list = []
        
        self.img = cv2.imread('test3.tiff', cv2.IMREAD_COLOR | cv2.IMREAD_ANYDEPTH)
        self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        self.img = cv2.flip(self.img, 0)

        print(self.img.shape)

        self.imview_orig = ImageViewClickable(self.point_list, size_hint=(0.5,0.8))
        self.imview_bg = ImageView(size_hint=(0.5,0.8))
        self.imview_orig.set_image(self.img)
        self.plview = PointListView(self.point_list)

        self.btn_calc = Button(text='Calculate Background Model')
        self.btn_calc.bind(on_press = self.btn_calc_press)

        self.add_widget(self.imview_orig)
        self.add_widget(self.imview_bg)
        self.add_widget(self.plview)
        self.add_widget(self.btn_calc)

    def on_touch_down(self, touch):

        self.plview.update_data(self.point_list)

        return super().on_touch_down(touch)

    def btn_calc_press(self, instance):
        x = []
        y = []
        r = []
        g = []
        b = []

        for point in self.point_list:
            point = np.array(point).astype(int)
            x.append(point[1])
            y.append(point[0])
            r.append(np.median(self.img[point[1]-self.sample_radius:point[1]+self.sample_radius, point[0]-self.sample_radius:point[0]+self.sample_radius, 0]))
            g.append(np.median(self.img[point[1]-self.sample_radius:point[1]+self.sample_radius, point[0]-self.sample_radius:point[0]+self.sample_radius, 1]))
            b.append(np.median(self.img[point[1]-self.sample_radius:point[1]+self.sample_radius, point[0]-self.sample_radius:point[0]+self.sample_radius, 2]))

        print(g)

        int_r = interp2d(x,y,r, kind = 'cubic')
        int_g = interp2d(x,y,g, kind = 'cubic')
        int_b = interp2d(x,y,b, kind = 'cubic')

        x_coord = np.arange(0, self.img.shape[0], 1)
        y_coord = np.arange(0, self.img.shape[1], 1)

        bkg_r = int_r(x_coord, y_coord)
        bkg_g = int_g(x_coord, y_coord)
        bkg_b = int_b(x_coord, y_coord)

        background = np.array([bkg_r, bkg_g, bkg_b])
        background = np.transpose(background, (2,1,0))
        background = np.asarray(background, dtype=np.float32)

        self.imview_bg.set_image(background)
        
class APBE(App):

    def build(self):
    
        return MyLayout(cols=2, rows=2)
        
  
apbe = APBE()
apbe.run()
