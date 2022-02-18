from turtle import back
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
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
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

class APBE_Instance():
    def __init__(self):
        self.img_original = 0
        self.img_background = 0
        self.point_list = []
        self.img_path = ''
        self.sample_radius = 5

    def set_img_original(self, img_original):
        self.img_original = img_original

    def set_img_background(self, img_background):
        self.img_background = img_background

    def add_sample_point(self, x,y):
        self.point_list.append(SamplePoint(x,y, self.img_original))

    def remove_sample_point(self, sample_point):
        self.point_list.remove(sample_point)

    def clear_sample_points(self):
        self.point_list.clear()

    def load_image(self, img_path):
        try:
            self.img_path = img_path

            self.img_original = cv2.imread(self.img_path, cv2.IMREAD_COLOR | cv2.IMREAD_ANYDEPTH)
            self.img_original = cv2.cvtColor(self.img_original, cv2.COLOR_BGR2RGB)
            self.img_original = cv2.flip(self.img_original, 0)
        except Exception as e:
            print('Something went wrong while loading the image:')
            print(e)



    def calculate_background(self):
        x = []
        y = []
        samples = []

        for sample_point in self.point_list:
            x.append(sample_point.x)
            y.append(sample_point.y)
            median = sample_point.calculate_sample_median(self.sample_radius)

            samples.append(median)
        
        samples = np.array(samples)

        try:
            background = np.zeros(self.img_original.shape)
            x_coord = np.arange(0, self.img_original.shape[0], 1)
            y_coord = np.arange(0, self.img_original.shape[1], 1)

            for c in range(self.img_original.shape[2]):
                interpolator = interp2d(x,y,samples[:, c], kind = 'cubic')
                background[:, :, c] = interpolator(x_coord, y_coord).transpose()

            background = np.transpose(background, (0, 1, 2))
            self.img_background = np.asarray(background, dtype=np.float32)

        except Exception as e:
            print('Something went wrong during calculating the background')
            print(e)


    def subtract_background(self):
        try:
            mean = np.mean(self.img_original, axis=(0,1,2))  
            self.img_original = self.img_original - self.img_background + mean
        except Exception as e:
            print('Something went wrong during subtracting the background')
            print(e) 
        


class SamplePoint():
    def __init__(self, x,y, img):
       self.x = x
       self.y = y
       self.img = img

    def calculate_sample_median(self, sample_radius):
        median = []

        # maybe do something more sophisticated here
        if self.x - sample_radius >= 0 and self.x + sample_radius < self.img.shape[0] and self.y - sample_radius >= 0 and self.y + sample_radius < self.img.shape[1]:
            for c in range(self.img.shape[2]):
                median.append(np.median(self.img[self.x - sample_radius : self.x + sample_radius, self.y - sample_radius : self.y + sample_radius, c]))

        return np.array(median)

class ControlView(GridLayout, StencilView):
    def __init__(self, apbe, imview_orig, imview_bg, **kwargs):
        StencilView.__init__(self, **kwargs)
        GridLayout.__init__(self, **kwargs)

        self.apbe = apbe
        self.imview_orig = imview_orig
        self.imview_bg = imview_bg

        self.btn_load = Button(text='Load 32bit TIFF')
        self.btn_load.bind(on_press = self.btn_load_press)
        self.btn_calc = Button(text='Calculate Background Model')
        self.btn_calc.bind(on_press = self.btn_calc_press)
        self.btn_sub = Button(text='Subtract Background')
        self.btn_sub.bind(on_press = self.btn_sub_press)

        self.add_widget(self.btn_load)
        self.add_widget(self.btn_calc)
        self.add_widget(self.btn_sub)

    def btn_load_press(self, instance):
        self.popup_layout = GridLayout(rows = 3)
        self.btn_open = Button(text = 'Open', size_hint = (1, 0.1))
        self.btn_cancel = Button(text = 'Cancel', size_hint = (1, 0.1))
        self.filechooser = FileChooserIconView(size_hint = (1, 0.8))

        self.popup_layout.add_widget(self.filechooser)
        self.popup_layout.add_widget(self.btn_open)
        self.popup_layout.add_widget(self.btn_cancel)

        self.load_popup = Popup(title = 'Load TIFF file', content = self.popup_layout)
        self.btn_cancel.bind(on_press = self.load_popup.dismiss)
        self.btn_open.bind(on_press = self.btn_open_press)

        self.load_popup.open()

    def btn_open_press(self, instance):
        self.apbe.load_image(self.filechooser.selection[0])

        self.imview_orig.set_image(self.apbe.img_original)

        self.load_popup.dismiss()
    
    def btn_sub_press(self, instance):
        self.apbe.subtract_background()
        self.imview_orig.set_image(self.apbe.img_original)

    def btn_calc_press(self, instance):
        self.apbe.calculate_background()
        self.imview_bg.set_image(self.apbe.img_background)
        


class PointListView(RecycleView):
    def __init__(self, apbe, **kwargs):
        super(PointListView, self).__init__(**kwargs)

        self.apbe = apbe
        self.data = [({'text': 'x = ' + str(sample_point.x) + ', y = ' + str(sample_point.y)}) for sample_point in self.apbe.point_list]
        self.viewclass = 'Label'

    def update_data(self):
        self.data = [({'text': 'x = ' + str(sample_point.x) + ', y = ' + str(sample_point.y)}) for sample_point in self.apbe.point_list]

class ImageView(StencilView):
    def __init__(self, apbe, **kwargs):
        super(ImageView, self).__init__(**kwargs)
        
        self.apbe = apbe

        self.sp = ScatterPlane()
        self.sp.do_translation=True

        self.add_widget(self.sp)

    def set_image(self, img):

        try:  
            w, h, channels = img.shape
            self.texture = Texture.create(size=(h,w))
            if channels == 1:
                self.texture.blit_buffer(img.flatten(), colorfmt='luminance', bufferfmt='float')
            elif channels == 3:
                self.texture.blit_buffer(img.flatten(), colorfmt='rgb', bufferfmt='float')
            else:
                print('Wrong amount of color channels in image')

            with self.sp.canvas:
                Rectangle(texture = self.texture, pos=(0,0), size=(h,w))
        
        except Exception as e:
            print('Something set wrang displaying the image:')
            print(e)

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
    def __init__(self, apbe, plview, **kwargs):
        super(ImageViewClickable, self).__init__(apbe, **kwargs)
        self.apbe = apbe
        self.plview = plview

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            if touch.button == 'right':
                with self.sp.canvas:
                    if self.sp.collide_point(touch.x, touch.y):
                        loc_x, loc_y = self.sp.to_local(int(touch.x), int(touch.y))
                        if loc_x > 0 and loc_x < self.apbe.img_original.shape[1] and loc_y > 0 and loc_y < self.apbe.img_original.shape[0]:
                            Color(1,0,0)
                            l = 24
                            Rectangle(pos=(loc_x - l/2, loc_y - l/2), size=(l,l))
                            Color(1,1,1)
                            # swap is intended
                            self.apbe.add_sample_point(int(loc_y), int(loc_x))
                            self.plview.update_data()

            super(ImageViewClickable, self).on_touch_down(touch)

class MyLayout(GridLayout):
    def __init__(self, apbe, **kwargs):
        super().__init__(**kwargs)
        self.apbe = apbe   

        self.plview = PointListView(self.apbe, size_hint=(0.5,0.2))
        self.imview_orig = ImageViewClickable(self.apbe, self.plview, size_hint=(0.5,0.8))
        self.imview_bg = ImageView(self.apbe, size_hint=(0.5,0.8))     
        self.ctrl_view = ControlView(self.apbe, self.imview_orig, self.imview_bg, rows=2, cols=2, size_hint=(0.5,0.2))

        self.add_widget(self.imview_orig)
        self.add_widget(self.imview_bg)
        self.add_widget(self.plview)
        self.add_widget(self.ctrl_view)

    def on_touch_down(self, touch):

        #self.plview.update_data()

        return super().on_touch_down(touch)
        
class APBE(App):

    def build(self):
        apbe = APBE_Instance()
        return MyLayout(apbe, cols=2, rows=2)
        
  
apbe = APBE()
apbe.run()
