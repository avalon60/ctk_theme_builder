import os
import sys
# Add the parent directory to the Python path
import tkinter as tk
import customtkinter
import argparse

from pathlib import Path
import model.ctk_theme_builder as mod
import model.preferences as pref
import threading
import time


prog_path = os.path.realpath(__file__)
app_home = Path(os.path.dirname(os.path.realpath(__file__)))

PROG = os.path.basename(__file__)

APP_HOME = mod.APP_HOME
ASSETS_DIR = mod.ASSETS_DIR
CONFIG_DIR = mod.CONFIG_DIR
ETC_DIR = mod.ETC_DIR
TEMP_DIR = mod.TEMP_DIR
VIEWS_DIR = mod.VIEWS_DIR
APP_THEMES_DIR = mod.APP_THEMES_DIR
APP_DATA_DIR = mod.APP_DATA_DIR
APP_IMAGES = mod.APP_IMAGES
DB_FILE_PATH = mod.DB_FILE_PATH


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        icon_photo = tk.PhotoImage(file=APP_IMAGES / 'bear-logo-colour-dark.png')
        self.iconphoto(False, icon_photo)
        # Restore preferences
        self.qa_geometry = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='window_geometry',
                                                   preference_name='qa_application')
        if self.qa_geometry == 'NO_DATA_FOUND':
            self.qa_geometry = '1100x580+0+0'
            self.qa_geometry_dict = pref.new_preference_dict(scope='window_geometry',
                                                             preference_name='qa_application',
                                                             data_type='str', preference_value=self.qa_geometry)
            pref.upsert_preference(db_file_path=DB_FILE_PATH, preference_row_dict=self.qa_geometry_dict)
        self.geometry(self.qa_geometry)

        self.qa_app_scaling = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='scaling',
                                                      preference_name='qa_application')
        if self.qa_app_scaling == 'NO_DATA_FOUND':
            self.qa_app_scaling = '100%'
            self.qa_app_scaling_dict = pref.new_preference_dict(scope='scaling',
                                                                preference_name='qa_application',
                                                                data_type='str', preference_value=self.qa_app_scaling)
            pref.upsert_preference(db_file_path=DB_FILE_PATH, preference_row_dict=self.qa_app_scaling_dict)

        self.change_scaling_event(self.qa_app_scaling)
        # configure window
        self.title("CTk Theme Builder Quality Assurance")
        theme_dict = mod.json_dict(theme_json_file)
        if 'provenance' in theme_dict:
            self.theme_name = theme_dict["provenance"]["theme name"]
        else:
            self.theme_name = os.path.basename(theme_json_file)

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text=self.theme_name,
                                                 font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, command=self.sidebar_button_event)
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, command=self.sidebar_button_event)
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)
        self.sidebar_button_3 = customtkinter.CTkButton(self.sidebar_frame, command=self.sidebar_button_event)
        self.sidebar_button_3.grid(row=3, column=0, padx=20, pady=10)
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame,
                                                                       values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))

        # create main entry and button
        self.entry = customtkinter.CTkEntry(self, placeholder_text="CTkEntry")
        self.entry.grid(row=3, column=1, columnspan=2, padx=(20, 0), pady=(20, 20), sticky="nsew")

        self.main_button_1 = customtkinter.CTkButton(master=self, text='Close', border_width=2, command=self.close_app)
        self.main_button_1.grid(row=3, column=3, padx=(20, 20), pady=(20, 20), sticky="nsew")

        # create textbox
        self.textbox = customtkinter.CTkTextbox(self, width=250)
        self.textbox.grid(row=0, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew")

        # create tabview
        self.tabview = customtkinter.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=2, padx=(20, 0), pady=(20, 0), sticky="nsew")
        self.tabview.add("CTkTabview")
        self.tabview.add("Tab 2")
        self.tabview.add("Tab 3")
        self.tabview.tab("CTkTabview").grid_columnconfigure(0, weight=1)  # configure grid of individual tabs
        self.tabview.tab("Tab 2").grid_columnconfigure(0, weight=1)

        self.optionmenu_1 = customtkinter.CTkOptionMenu(self.tabview.tab("CTkTabview"), dynamic_resizing=False,
                                                        values=["Value 1", "Value 2", "Value Long Long Long"])
        self.optionmenu_1.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.combobox_1 = customtkinter.CTkComboBox(self.tabview.tab("CTkTabview"),
                                                    values=["Value 1", "Value 2", "Value Long....."])
        self.combobox_1.grid(row=1, column=0, padx=20, pady=(10, 10))
        self.string_input_button = customtkinter.CTkButton(self.tabview.tab("CTkTabview"), text="Open CTkInputDialog",
                                                           command=self.open_input_dialog_event)
        self.string_input_button.grid(row=2, column=0, padx=20, pady=(10, 10))
        self.label_tab_2 = customtkinter.CTkLabel(self.tabview.tab("Tab 2"), text="CTkLabel on Tab 2")
        self.label_tab_2.grid(row=0, column=0, padx=20, pady=20)

        # create radiobutton frame
        self.radiobutton_frame = customtkinter.CTkFrame(self)
        self.radiobutton_frame.grid(row=0, column=3, padx=(20, 20), pady=(20, 0), sticky="nsew")
        self.radio_var = tk.IntVar(value=0)
        self.label_radio_group = customtkinter.CTkLabel(master=self.radiobutton_frame, text="CTkRadioButton Group:")
        self.label_radio_group.grid(row=0, column=2, columnspan=1, padx=10, pady=10, sticky="")
        self.radio_button_1 = customtkinter.CTkRadioButton(master=self.radiobutton_frame, variable=self.radio_var,
                                                           value=0)
        self.radio_button_1.grid(row=1, column=2, pady=10, padx=20, sticky="n")
        self.radio_button_2 = customtkinter.CTkRadioButton(master=self.radiobutton_frame, variable=self.radio_var,
                                                           value=1)
        self.radio_button_2.grid(row=2, column=2, pady=10, padx=20, sticky="n")
        self.radio_button_3 = customtkinter.CTkRadioButton(master=self.radiobutton_frame, variable=self.radio_var,
                                                           value=2)
        self.radio_button_3.grid(row=3, column=2, pady=10, padx=20, sticky="n")

        # create slider and progressbar frame
        self.slider_progressbar_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.slider_progressbar_frame.grid(row=1, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew")
        self.slider_progressbar_frame.grid_columnconfigure(0, weight=1)
        self.slider_progressbar_frame.grid_rowconfigure(4, weight=1)
        self.seg_button_1 = customtkinter.CTkSegmentedButton(self.slider_progressbar_frame)
        self.seg_button_1.grid(row=0, column=0, padx=(20, 10), pady=(10, 10), sticky="ew")
        self.progressbar_1 = customtkinter.CTkProgressBar(self.slider_progressbar_frame)
        self.progressbar_1.grid(row=1, column=0, padx=(20, 10), pady=(10, 10), sticky="ew")
        self.progressbar_2 = customtkinter.CTkProgressBar(self.slider_progressbar_frame)
        self.progressbar_2.grid(row=2, column=0, padx=(20, 10), pady=(10, 10), sticky="ew")
        self.slider_1 = customtkinter.CTkSlider(self.slider_progressbar_frame, from_=0, to=1, number_of_steps=4)
        self.slider_1.grid(row=3, column=0, padx=(20, 10), pady=(10, 10), sticky="ew")
        self.slider_2 = customtkinter.CTkSlider(self.slider_progressbar_frame, orientation="vertical")
        self.slider_2.grid(row=0, column=1, rowspan=5, padx=(10, 10), pady=(10, 10), sticky="ns")
        self.progressbar_3 = customtkinter.CTkProgressBar(self.slider_progressbar_frame, orientation="vertical")
        self.progressbar_3.grid(row=0, column=2, rowspan=5, padx=(10, 20), pady=(10, 10), sticky="ns")

        # create scrollable frame
        self.scrollable_frame = customtkinter.CTkScrollableFrame(self, label_text="CTkScrollableFrame")
        self.scrollable_frame.grid(row=1, column=2, padx=(20, 0), pady=(20, 0), sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame_switches = []
        for i in range(100):
            switch = customtkinter.CTkSwitch(master=self.scrollable_frame, text=f"CTkSwitch {i}")
            switch.grid(row=i, column=0, padx=10, pady=(0, 20))
            self.scrollable_frame_switches.append(switch)

        # create checkbox and switch frame
        self.checkbox_slider_frame = customtkinter.CTkFrame(self)
        self.checkbox_slider_frame.grid(row=1, column=3, padx=(20, 20), pady=(20, 0), sticky="nsew")
        self.checkbox_1 = customtkinter.CTkCheckBox(master=self.checkbox_slider_frame)
        self.checkbox_1.grid(row=1, column=0, pady=(20, 0), padx=20, sticky="n")
        self.checkbox_2 = customtkinter.CTkCheckBox(master=self.checkbox_slider_frame)
        self.checkbox_2.grid(row=2, column=0, pady=(20, 0), padx=20, sticky="n")
        self.checkbox_3 = customtkinter.CTkCheckBox(master=self.checkbox_slider_frame)
        self.checkbox_3.grid(row=3, column=0, pady=20, padx=20, sticky="n")

        # set default values
        self.sidebar_button_3.configure(state="disabled", text="Disabled CTkButton")
        self.checkbox_3.configure(state="disabled")
        self.checkbox_1.select()
        self.scrollable_frame_switches[0].select()
        self.scrollable_frame_switches[4].select()
        self.radio_button_3.configure(state="disabled")
        mode = customtkinter.get_appearance_mode()
        self.appearance_mode_optionemenu.set(mode)
        self.optionmenu_1.set("CTkOptionmenu")
        self.combobox_1.set("CTkComboBox")
        self.slider_1.configure(command=self.progressbar_2.set)
        self.slider_2.configure(command=self.progressbar_3.set)
        self.progressbar_1.configure(mode="indeterminnate")
        self.progressbar_1.start()
        self.textbox.insert("0.0",
                            "CTkTextbox\n\n" + "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua.\n\n" * 20)
        self.seg_button_1.configure(values=["CTkSegmentedButton", "Value 2", "Value 3"])
        self.seg_button_1.set("Value 2")
        self.protocol("WM_DELETE_WINDOW", self.close_app)

        self.keep_running = True

        # Signal that we have started the app
        mod.qa_app_started()
        self.after(100, self.check_for_running)
        self.start_requested_close_listener()

        self.bind('<Escape>', self.close_app)

    def check_for_running(self):
        if not self.keep_running:
            self.close_app()
        else:
            self.after(100, self.check_for_running)

    def start_requested_close_listener(self):
        """Listener, which checks to see if a close request file has been created."""
        client_thread = threading.Thread(target=self.listen_for_close,
                                         daemon=True)
        client_thread.start()

    def open_input_dialog_event(self):
        dialog = customtkinter.CTkInputDialog(text="Type in a number:", title="CTkInputDialog")
        print("CTkInputDialog:", dialog.get_input())

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    def close_app(self, event=None):
        self.save_app_geometry()
        mod.complete_qa_stop()
        self.destroy()

    def listen_for_close(self):
        while 1:
            if mod.close_qa_app_requested():
                mod.complete_qa_stop()
                self.keep_running = False
            time.sleep(0.1)

    def save_app_geometry(self):
        """Save the control panel geometry to the repo, for the next time the program is launched."""
        geometry_row = pref.preference_row(db_file_path=DB_FILE_PATH,
                                           scope='window_geometry',
                                           preference_name='qa_application')
        qa_geometry = self.geometry()
        geometry_row["preference_value"] = qa_geometry
        pref.upsert_preference(db_file_path=DB_FILE_PATH, preference_row_dict=geometry_row)

    @staticmethod
    def sidebar_button_event():
        print("sidebar_button click")


ap = argparse.ArgumentParser(description=f"""{PROG}: CTk Theme Builder test app.""")

ap.add_argument("-a", "--appearance_mode", required=False, action="store",
                help=f'Specifies the location of the theme file to use.',
                dest='appearance_mode', default='Light')

ap.add_argument("-t", "--theme-json-file", required=True, action="store",
                help=f'Specifies the location of the theme file to use.',
                dest='theme_json_file')

args_list = vars(ap.parse_args())

appearance_mode = args_list["appearance_mode"]
theme_json_file = args_list["theme_json_file"]

customtkinter.set_appearance_mode(appearance_mode)  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme(theme_json_file)

if __name__ == "__main__":
    app = App()
    app.mainloop()
