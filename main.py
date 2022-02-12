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
                        l = 10
                        Rectangle(pos=(loc_x - l/2, loc_y - l/2), size=(l,l), color=(1,0,0))

                        self.point_list.append((loc_x, loc_y))
                        print(self.point_list)

            super(ImageViewClickable, self).on_touch_down(touch)

class MyLayout(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.sample_size=5

        self.point_list = []
        
        self.img = cv2.imread('test3.tiff', cv2.IMREAD_COLOR | cv2.IMREAD_ANYDEPTH)
        self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        self.img = cv2.flip(self.img, 0)

        self.imview_orig = ImageViewClickable(self.point_list, size_hint=(0.5,0.8))
        self.imview_bg = ImageView(size_hint=(0.5,0.8))
        self.imview_orig.set_image(self.img)
        self.plview = PointListView(self.point_list)
        self.plview2 = PointListView(self.point_list)

        self.btn_calc = Button(text='Calculate Background Model')
        self.btn_calc.bind(on_press = self.btn_calc_press)

        self.add_widget(self.imview_orig)
        self.add_widget(self.imview_bg)
        self.add_widget(self.plview)
        self.add_widget(self.btn_calc)
        #self.add_widget(self.plview2)

    def on_touch_down(self, touch):

        self.plview.update_data(self.point_list)

        return super().on_touch_down(touch)

    def btn_calc_press(self, instance):
        print('Button pressed')
        
class APBE(App):

    # This returns the content we want in the window
    def build(self):
    
        return MyLayout(cols=2, rows=2)
        
  
apbe = APBE()
apbe.run()
