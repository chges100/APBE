from matplotlib.widgets import Widget
import numpy as np
from PIL import Image

import kivy
kivy.require('1.10.0')
  
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.uix.scatter import ScatterPlane
from kivy.uix.recycleview import RecycleView
from kivy.uix.boxlayout import BoxLayout
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
        self.data = [({'text': str(point)}) for point in []]
        #self.data = [({'text': str(point)}) for point in point_list]

class ImageView(Widget):
    def __init__(self, img, point_list, **kwargs):
        super(ImageView, self).__init__(**kwargs)

        self.img = img
        self.point_list = point_list

        w, h, _ = self.img.shape
        self.texture = Texture.create(size=(h,w))
        self.texture.blit_buffer(self.img.flatten(), colorfmt='rgb', bufferfmt='float')

        self.sp = ScatterPlane()
        with self.sp.canvas:
            Rectangle(texture = self.texture, pos=self.pos, size=(h,w))
        #self.sp.add_widget(self.w_img)
        self.add_widget(self.sp)


    def on_touch_down(self, touch):
        if touch.is_mouse_scrolling:
            if touch.button == 'scrolldown':
                if self.sp.scale < 10:
                    self.sp.scale = self.sp.scale * 1.1
            elif touch.button == 'scrollup':
                #if self.sp.scale > 1:
                self.sp.scale = self.sp.scale * 0.8
        elif touch.button == 'left':
            super(ImageView, self).on_touch_down(touch)

        elif touch.button == 'right':
            with self.sp.canvas:
                if self.sp.collide_point(touch.x, touch.y):
                    loc_x, loc_y = self.sp.to_local(touch.x, touch.y)
                    Color(1,0,0)
                    l = 10
                    Rectangle(pos=(loc_x - l/2, loc_y - l/2), size=(l,l))

                    self.point_list.append((loc_x, loc_y))
                    print(self.point_list)

class MyLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.point_list = []
        
        img = cv2.imread('test3.tiff', cv2.IMREAD_COLOR | cv2.IMREAD_ANYDEPTH)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.flip(img, 0)

        self.imview = ImageView(img, self.point_list)
        self.plview = PointListView(self.point_list)

        self.add_widget(self.imview)
        self.add_widget(self.plview)

    def on_touch_down(self, touch):
        if self.imview.collide_point(touch.x, touch.y):
            self.imview.on_touch_down(touch)

        self.plview.update_data(self.point_list)

        return super().on_touch_down(touch)
        


class APBE(App):

    # This returns the content we want in the window
    def build(self):
    
        return MyLayout()
        
  
apbe = APBE()
apbe.run()
