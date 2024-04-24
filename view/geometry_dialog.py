"""Class container for GeometryDialog class"""

import customtkinter as ctk
import tkinter as tk
import utils.cbtk_kit as cbtk
import model.ctk_theme_builder as mod
from model.ctk_theme_builder import log_call
from view.ctk_theme_preview import update_widget_geometry
import json
import utils.loggerutl as log
from pathlib import Path
from CTkToolTip import *
import model.preferences as pref

ETC_DIR = mod.ETC_DIR
DB_FILE_PATH = mod.DB_FILE_PATH


class GeometryDialog(ctk.CTkToplevel):

    def __init__(self, widget_type: str, theme_json_data: dict, appearance_mode: str,
                 command_stack: mod.CommandStack, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_stack = command_stack
        self.force_refresh = False
        log.log_debug(log_text='Geometry dialog launched.')

        self.enable_tooltips = pref.preference_setting(db_file_path=DB_FILE_PATH, scope='user_preference',
                                                       preference_name='enable_tooltips')

        # The interactions between this dialog and the Control Panel are strongly linked, making it less
        # straight forward to define as a class.
        @log_call
        def slider_callback(property_name, value):
            label_text = property_name.replace('_', ' ')
            base_label_text = label_text.replace(widget_type.lower(), '') + ': '
            property_value = int(value)
            label_dict[property_name].configure(text=base_label_text + str(property_value))
            config_param = property_name.replace(f'{widget_type.lower()}_', '')
            self.geometry_edit_values[property_name] = property_value

            if config_param == 'border_width_unchecked':
                geometry_widget.deselect()
            elif config_param == 'border_width_checked':
                geometry_widget.select()

            update_widget_geometry(widget=geometry_widget, widget_property=config_param, property_value=property_value)

        @log_call
        def deselect_widget(widget_id):
            """This local function is provided as a means to deselect the CTkRadioButton. This is for when the user
            clicks on the rendered button, in the geometry edit dialogue, and they subsequently need to show it
            de-selected."""
            widget_id.deselect()

        self.appearance_mode = appearance_mode
        self.theme_json_data = theme_json_data
        self.geometry_edit_values = {}
        preview_frame_top = self.theme_json_data['CTkFrame']['top_fg_color'][
            cbtk.str_mode_to_int(self.appearance_mode)]

        self.title(f'{widget_type} Widget Geometry')

        self.restore_geom_geometry()

        # Make preferences dialog modal
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        # self.columnconfigure(0, weight=0)
        # self.columnconfigure(1, weight=1)

        preview_text_colour = self.theme_json_data['CTkLabel']['text_color'][
            cbtk.str_mode_to_int(self.appearance_mode)]

        frm_main = ctk.CTkFrame(master=self, corner_radius=5)
        frm_main.grid(column=0, row=0, sticky='nsew')
        frm_main.columnconfigure(0, weight=0)
        frm_main.columnconfigure((1, 2), weight=1)
        frm_main.rowconfigure(0, weight=1)

        frame_fg_color = self.theme_json_data['CTkFrame']['fg_color'][
            cbtk.str_mode_to_int(self.appearance_mode)]
        # json_widget_type = mod.json_widget_type(widget_type=widget_type)
        json_widget_type = widget_type
        mode = cbtk.str_mode_to_int(self.appearance_mode)
        if widget_type == 'CTkFrame':
            # self.geometry('764x280')
            frm_widget_preview_low = ctk.CTkFrame(master=frm_main,
                                                  fg_color=cbtk.contrast_colour(preview_frame_top, 20),
                                                  width=250,
                                                  height=250
                                                  )
            frm_main.configure(corner_radius=self.theme_json_data[widget_type]['corner_radius'])
        else:
            frm_widget_preview_low = ctk.CTkFrame(master=frm_main,
                                                  corner_radius=5,
                                                  fg_color=preview_frame_top)

        frm_widget_preview_low.grid(column=1, row=0, padx=10, pady=10, sticky='nsew')

        frm_controls = ctk.CTkFrame(master=frm_main)
        frm_controls.grid(column=0, row=0, padx=10, pady=10, sticky='nsew')

        frm_buttons = ctk.CTkFrame(master=frm_main)
        frm_buttons.grid(column=0, row=1, padx=10, pady=(0, 10), sticky='ew')

        frm_label = ctk.CTkFrame(master=frm_main)
        frm_label.grid(column=1, row=1, padx=10, pady=(0, 10), sticky='ew')

        widget_label = ctk.CTkLabel(master=frm_label, text=f'{widget_type} Geometry',
                                    font=mod.HEADING5,
                                    justify=ctk.CENTER)
        widget_label.grid(row=0, column=0, padx=(30, 30), pady=(5, 5), sticky='ew')

        # Control buttons
        btn_close = ctk.CTkButton(master=frm_buttons, text='Cancel', command=self.close_geometry_dialog)
        btn_close.grid(row=0, column=0, padx=(25, 35), pady=5)

        btn_save = ctk.CTkButton(master=frm_buttons, text='Save',
                                 command=lambda w_type=widget_type: self.save_geometry_edits(widget_type=w_type))
        btn_save.grid(row=0, column=1, padx=(160, 15), pady=5)

        geometry_parameters_file = str(ETC_DIR / 'geometry_parameters.json')
        geometry_parameters_file = Path(geometry_parameters_file)
        geometry_parameters_file_json = mod.json_dict(json_file_path=geometry_parameters_file)
        self.bind('<Escape>', self.close_geometry_dialog)

        if widget_type == 'CTkButton':
            # self.geometry('764x234')
            button_text_colour = self.theme_json_data[json_widget_type]['text_color'][mode]
            button_fg_colour = self.theme_json_data[json_widget_type]['fg_color'][mode]
            button_hover_colour = self.theme_json_data[json_widget_type]['hover_color'][mode]
            button_border_colour = self.theme_json_data[json_widget_type]['border_color'][mode]

            geometry_widget = ctk.CTkButton(master=frm_widget_preview_low,
                                            text_color=button_text_colour,
                                            fg_color=button_fg_colour,
                                            hover_color=button_hover_colour,
                                            border_color=button_border_colour,
                                            text='CTkButton',
                                            corner_radius=self.theme_json_data['CTkButton']['corner_radius'],
                                            border_width=self.theme_json_data['CTkButton']['border_width'])
        elif widget_type == 'CTkCheckBox':
            # self.geometry('786x232')
            checkbox_fg_color = self.theme_json_data['CTkCheckBox']['fg_color'][mode]

            checkbox_border_color = self.theme_json_data['CTkCheckBox']['border_color'][mode]

            checkbox_hover_color = self.theme_json_data['CTkCheckBox']['hover_color'][mode]

            checkbox_checkmark_color = self.theme_json_data['CTkCheckBox']['checkmark_color'][mode]

            checkbox_text_color = self.theme_json_data['CTkCheckBox']['text_color'][mode]

            geometry_widget = ctk.CTkCheckBox(master=frm_widget_preview_low,
                                              fg_color=checkbox_fg_color,
                                              border_color=checkbox_border_color,
                                              hover_color=checkbox_hover_color,
                                              checkmark_color=checkbox_checkmark_color,
                                              text_color=checkbox_text_color,
                                              corner_radius=self.theme_json_data['CTkCheckBox']['corner_radius'],
                                              border_width=self.theme_json_data['CTkCheckBox']['border_width'])
        elif widget_type == 'CTkComboBox':
            # self.geometry('795x234')

            combobox_fg_color = self.theme_json_data['CTkComboBox']['fg_color'][mode]

            combobox_text_color = self.theme_json_data['CTkComboBox']['text_color'][mode]

            combobox_border_color = self.theme_json_data['CTkComboBox']['border_color'][mode]

            combobox_button_colour = self.theme_json_data[json_widget_type]['button_color'][mode]

            combobox_button_hover_colour = self.theme_json_data[json_widget_type]['button_hover_color'][mode]

            dropdown_fg_colour = self.theme_json_data['DropdownMenu']['fg_color'][mode]

            dropdown_hover_colour = self.theme_json_data['DropdownMenu']['hover_color'][mode]

            dropdown_text_colour = self.theme_json_data['DropdownMenu']['text_color'][mode]

            geometry_widget = ctk.CTkComboBox(master=frm_widget_preview_low,
                                              fg_color=combobox_fg_color,
                                              text_color=combobox_text_color,
                                              border_color=combobox_border_color,
                                              button_color=combobox_button_colour,
                                              button_hover_color=combobox_button_hover_colour,
                                              dropdown_fg_color=dropdown_fg_colour,
                                              dropdown_text_color=dropdown_text_colour,
                                              dropdown_hover_color=dropdown_hover_colour,
                                              corner_radius=self.theme_json_data['CTkCheckBox']['corner_radius'],
                                              border_width=self.theme_json_data['CTkCheckBox']['border_width'],
                                              values=["Option 1", "Option 2", "Option 3", "Option 4..."])
        elif widget_type == 'CTkFrame':
            # self.geometry('764x280')
            geometry_widget = ctk.CTkFrame(master=frm_widget_preview_low, fg_color=preview_frame_top,
                                           corner_radius=self.theme_json_data['CTkFrame']['corner_radius'],
                                           border_width=self.theme_json_data['CTkFrame']['border_width'])

            lbl_frame = ctk.CTkLabel(master=geometry_widget, text_color=preview_text_colour, text='CTKFrame')
            lbl_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        elif widget_type == 'CTkLabel':
            # self.geometry('755x160')
            geometry_widget = ctk.CTkLabel(master=frm_widget_preview_low,
                                           text_color=preview_text_colour,
                                           fg_color=cbtk.contrast_colour(preview_frame_top, 15),
                                           corner_radius=self.theme_json_data[widget_type]['corner_radius'])
            widget_tooltip = CTkToolTip(geometry_widget, wraplength=200,
                                        border_width=1,
                                        justify="left",
                                        padding=(10, 10),
                                        corner_radius=6,
                                        message='The CTkLabel widget has been intentionally '
                                                'rendered with a contrasting fg_color, so that '
                                                'the corner radius effect may be seen.')
        elif widget_type == 'CTkEntry':
            fg_color = self.theme_json_data['CTkEntry']['fg_color'][mode]
            border_color = self.theme_json_data['CTkEntry']['border_color'][mode]
            # self.geometry('754x235')
            geometry_widget = ctk.CTkEntry(master=frm_widget_preview_low,
                                           placeholder_text="CTkEntry",
                                           fg_color=fg_color,
                                           border_color=border_color)

        elif widget_type == 'CTkProgressBar':
            # self.geometry('807x225')
            progressbar_fg_color = self.theme_json_data['CTkProgressBar']['fg_color'][mode]

            progressbar_progress_color = self.theme_json_data['CTkProgressBar']['progress_color'][mode]

            progressbar_border_color = self.theme_json_data['CTkProgressBar']['border_color'][mode]
            geometry_widget = ctk.CTkProgressBar(master=frm_widget_preview_low,
                                                 fg_color=progressbar_fg_color,
                                                 progress_color=progressbar_progress_color,
                                                 border_color=progressbar_border_color,
                                                 corner_radius=self.theme_json_data[json_widget_type]
                                                 ['corner_radius'],
                                                 border_width=self.theme_json_data[json_widget_type]
                                                 ['border_width'])
        elif widget_type == 'CTkSlider':
            # self.geometry('760x301')
            geometry_widget = ctk.CTkSlider(master=frm_widget_preview_low,
                                            border_width=self.theme_json_data[widget_type]['border_width'])

        elif widget_type == 'CTkOptionMenu':
            # self.geometry('806x161')

            optionmenu_fg_colour = self.theme_json_data[json_widget_type]['fg_color'][mode]

            optionmenu_button_colour = self.theme_json_data[json_widget_type]['button_color'][mode]

            optionmenu_button_hover_colour = self.theme_json_data[json_widget_type]['button_hover_color'][mode]

            optionmenu_text_color = self.theme_json_data[json_widget_type]['text_color'][mode]

            dropdown_fg_colour = self.theme_json_data['DropdownMenu']['fg_color'][mode]

            dropdown_hover_colour = self.theme_json_data['DropdownMenu']['hover_color'][mode]

            dropdown_text_colour = self.theme_json_data['DropdownMenu']['text_color'][mode]

            geometry_widget = ctk.CTkOptionMenu(master=frm_widget_preview_low,
                                                fg_color=optionmenu_fg_colour,
                                                text_color=optionmenu_text_color,
                                                button_color=optionmenu_button_colour,
                                                button_hover_color=optionmenu_button_hover_colour,
                                                dropdown_fg_color=dropdown_fg_colour,
                                                dropdown_text_color=dropdown_text_colour,
                                                dropdown_hover_color=dropdown_hover_colour,
                                                corner_radius=self.theme_json_data['CTkOptionMenu']['corner_radius'],
                                                values=["Option 1", "Option 2", "Option 3..."])
            geometry_widget.set("CTkOptionMenu")


        elif widget_type == 'CTkRadioButton':
            # self.geometry('800x301')
            radiobutton_fg_color = self.theme_json_data['CTkRadioButton']['fg_color'][mode]

            radiobutton_border_color = self.theme_json_data['CTkRadioButton']['border_color'][mode]

            radiobutton_hover_color = self.theme_json_data['CTkRadioButton']['hover_color'][mode]

            radiobutton_text_color = self.theme_json_data['CTkRadioButton']['text_color'][mode]

            label_text_colour = self.theme_json_data['CTkLabel']['text_color'][mode]

            geometry_widget = ctk.CTkRadioButton(master=frm_widget_preview_low,
                                                 fg_color=radiobutton_fg_color,
                                                 border_color=radiobutton_border_color,
                                                 hover_color=radiobutton_hover_color,
                                                 text_color=radiobutton_text_color,
                                                 corner_radius=self.theme_json_data[json_widget_type]
                                                 ['corner_radius'],
                                                 border_width_checked=self.theme_json_data[json_widget_type]
                                                 ['border_width_checked'],
                                                 border_width_unchecked=self.theme_json_data[json_widget_type]
                                                 ['border_width_unchecked'])
            lbl_info = ctk.CTkLabel(master=frm_widget_preview_low,
                                    text_color=label_text_colour,
                                    text='Use a right button click, to\nuncheck the radio '
                                         'button.', justify=ctk.CENTER)
            lbl_info.grid(row=0, column=0, padx=50, pady=10)

            geometry_widget.bind("<Button-3>", lambda event, widget=geometry_widget: deselect_widget(widget_id=widget))
        elif widget_type == 'CTkSegmentedButton':
            # self.geometry('847x232')
            # CTkTextbox
            seg_fg_color = self.theme_json_data[json_widget_type]['fg_color'][mode]
            seg_selected_color = self.theme_json_data[json_widget_type]['selected_color'][mode]
            seg_selected_hover_color = self.theme_json_data[json_widget_type]['selected_hover_color'][mode]
            seg_unselected_color = self.theme_json_data[json_widget_type]['unselected_color'][mode]
            seg_unselected_hover_color = self.theme_json_data[json_widget_type]['unselected_hover_color'][mode]
            seg_text_color = self.theme_json_data[json_widget_type]['text_color'][mode]
            seg_text_color_disabled = self.theme_json_data[json_widget_type]['text_color_disabled'][mode]

            geometry_widget = ctk.CTkSegmentedButton(master=frm_widget_preview_low,
                                                     fg_color=seg_fg_color,
                                                     selected_color=seg_selected_color,
                                                     selected_hover_color=seg_selected_hover_color,
                                                     unselected_color=seg_unselected_color,
                                                     unselected_hover_color=seg_unselected_hover_color,
                                                     text_color=seg_text_color,
                                                     text_color_disabled=seg_text_color_disabled)
            geometry_widget.grid(row=10, column=0, padx=(15, 0), pady=(30, 0), sticky="nsew", rowspan=1)

            geometry_widget.configure(values=["CTkSegmentedButton", "Value 2", "Value 3"])
            geometry_widget.set("Value 2")

        elif widget_type == 'CTkSwitch':
            # self.geometry('766x299')
            switch_fg_colour = self.theme_json_data[json_widget_type]['fg_color'][mode]

            switch_button_colour = self.theme_json_data[json_widget_type]['button_color'][mode]

            switch_button_hover_colour = self.theme_json_data[json_widget_type]['button_hover_color'][mode]

            switch_progress_colour = self.theme_json_data[json_widget_type]['progress_color'][mode]

            switch_text_colour = self.theme_json_data[json_widget_type]['text_color'][mode]

            geometry_widget = ctk.CTkSwitch(master=frm_widget_preview_low,
                                            fg_color=switch_fg_colour,
                                            button_color=switch_button_colour,
                                            text_color=switch_text_colour,
                                            button_hover_color=switch_button_hover_colour,
                                            progress_color=switch_progress_colour,
                                            corner_radius=self.theme_json_data[json_widget_type]['corner_radius'],
                                            border_width=self.theme_json_data[json_widget_type]['border_width']
                                            )
        elif widget_type == 'CTkScrollbar':
            # self.geometry('782x267')
            # Harness the scrollbar incorporated
            # to the CTkScrollableFrame widget.
            self.geometry('800x280')
            scrollbar_fg_color = self.theme_json_data[json_widget_type]['fg_color']
            if not isinstance(scrollbar_fg_color, str):
                scrollbar_fg_color = scrollbar_fg_color[cbtk.str_mode_to_int(self.appearance_mode)]
            elif scrollbar_fg_color == "transparent":
                scrollbar_fg_color = self.theme_json_data['CTkFrame']['fg_color'][
                    cbtk.str_mode_to_int(self.appearance_mode)]
            scrollbar_button_color = self.theme_json_data[json_widget_type]['button_color']
            scrollbar_button_hover_color = self.theme_json_data[json_widget_type]['button_hover_color']

            frm_preview = ctk.CTkFrame(frm_widget_preview_low, corner_radius=0)
            frm_preview.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

            # create textbox
            textbox_fg_color = self.theme_json_data['CTkTextbox']['fg_color'][
                cbtk.str_mode_to_int(self.appearance_mode)]
            if not isinstance(textbox_fg_color, str):
                textbox_fg_color = textbox_fg_color[cbtk.str_mode_to_int(self.appearance_mode)]
            textbox_border_color = self.theme_json_data['CTkTextbox']['border_color'][
                cbtk.str_mode_to_int(self.appearance_mode)]
            textbox_text_color = self.theme_json_data['CTkTextbox']['text_color'][
                cbtk.str_mode_to_int(self.appearance_mode)]
            tk_textbox = ctk.CTkTextbox(frm_preview,
                                        activate_scrollbars=False,
                                        fg_color=textbox_fg_color,
                                        border_color=textbox_border_color,
                                        text_color=textbox_text_color,
                                        corner_radius=0)
            tk_textbox.grid(row=0, column=1, sticky="nsew")
            tk_textbox.insert("0.0", text="CTkScrollBar\n\n" + "Bozzy bear woz here...\n\n" * 20)

            # create CTk scrollbar
            geometry_widget = ctk.CTkScrollbar(frm_preview,
                                               command=tk_textbox.yview,
                                               fg_color=scrollbar_fg_color,
                                               button_color=scrollbar_button_color,
                                               button_hover_color=scrollbar_button_hover_color)
            geometry_widget.grid(row=0, column=2, sticky="ns")
            tk_textbox.configure(yscrollcommand=geometry_widget.set)

        elif widget_type == 'CTkTextbox':
            # self.geometry('776x243')
            # CTkTextbox
            textbox_fg_color = self.theme_json_data[json_widget_type]['fg_color'][mode]
            if not isinstance(textbox_fg_color, str):
                textbox_fg_color = textbox_fg_color[cbtk.str_mode_to_int(self.appearance_mode)][mode]
            elif textbox_fg_color == "transparent":
                textbox_fg_color = self.theme_json_data['CTkFrame']['fg_color'][mode]
            textbox_border_color = self.theme_json_data[json_widget_type]['border_color'][mode]
            textbox_button_color = self.theme_json_data[json_widget_type]['scrollbar_button_color'][mode]
            textbox_button_hover_color = self.theme_json_data[json_widget_type]['scrollbar_button_hover_color'][mode]
            textbox_text_color = self.theme_json_data[json_widget_type]['text_color'][mode]

            geometry_widget = ctk.CTkTextbox(frm_widget_preview_low,
                                             fg_color=textbox_fg_color,
                                             border_color=textbox_border_color,
                                             scrollbar_button_color=textbox_button_color,
                                             scrollbar_button_hover_color=textbox_button_hover_color,
                                             text_color=textbox_text_color,
                                             width=190,
                                             height=180)
            geometry_widget.grid(row=10, column=0, padx=(15, 0), pady=(30, 0), sticky="nsew", rowspan=1)
            if self.enable_tooltips:
                textbox_tooltip = CTkToolTip(geometry_widget,
                                             wraplength=300,
                                             padding=(10, 10),
                                             corner_radius=6,
                                             x_offset=-100,
                                             justify="left",
                                             border_width=1,
                                             message='CTkTextbox')

            geometry_widget.insert("0.0", "CTkTextbox\n\n" + "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, "
                                                             "sed diam nonumy eirmod tempor invidunt ut labore et "
                                                             "dolore magna aliquyam erat, sed diam voluptua.\n\n" * 20)

        else:
            print(f'WARNING: unimplemented widget type: {widget_type}')

        if widget_type not in ['CTkScrollbar']:
            # geometry_widget.grid(row=0, column=0)
            geometry_widget.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        widget_parameter = geometry_parameters_file_json[widget_type]
        slider_dict = {}
        label_dict = {}
        property_value_dict = {}
        row = 0

        for property, parameters in widget_parameter.items():
            lower_value = int(parameters[0])
            upper_value = int(parameters[1])
            label_text = property.replace('_', ' ')
            base_label_text = label_text.replace(widget_type.lower(), '') + ': '
            # This function call is necessary, because there are several naming
            # inconsistencies (at least in CTk 5.1.2), between widget names.
            # json_widget_type = mod.json_widget_type(widget_type=widget_type)
            json_widget_type = widget_type

            current_value = int(self.theme_json_data[json_widget_type][property])
            label_dict[property] = ctk.CTkLabel(master=frm_controls, text=base_label_text.title() + f'{current_value}')
            label_dict[property].grid(row=row, column=0, sticky='ew', pady=(10, 0))
            row += 1

            slider_dict[property] = ctk.CTkSlider(master=frm_controls,
                                                  from_=lower_value, to=upper_value,
                                                  width=450, number_of_steps=(upper_value - lower_value),
                                                  command=lambda value, label_id=property: slider_callback(label_id,
                                                                                                           value))
            slider_dict[property].grid(row=row, column=0, padx=(25, 25), pady=(0, 15))
            slider_dict[property].set(current_value)
            row += 1

        self.wait_window()

    @log_call
    def save_geometry_edits(self, widget_type):
        self.force_refresh = False
        for widget_property, property_value in self.geometry_edit_values.items():
            parameters = []
            # This function call is necessary, because there are several naming
            # inconsistencies (at least in CTk 5.1.2), between widget names.
            if self.theme_json_data[widget_type][widget_property] != property_value:
                self.master.json_state = 'dirty'

                # Create ourselves a change vector - needed for undo / redo
                change_vector = mod.PropertyVector(command_type='geometry',
                                                   command='update_widget_geometry',
                                                   component_type=widget_type,
                                                   component_property=widget_property,
                                                   new_value=property_value,
                                                   old_value=self.theme_json_data[widget_type][widget_property])

                self.command_stack.exec_command(property_vector=change_vector)
                display_property = mod.PropertyVector.display_property(widget_type=widget_type,
                                                                       widget_property=widget_property)
                if display_property in mod.FORCE_GEOM_REFRESH_PROPERTIES:
                    self.force_refresh = True
                self.theme_json_data[widget_type][widget_property] = property_value

        if self.master.json_state == 'dirty':
            with open(self.master.wip_json, "w") as f:
                json.dump(self.theme_json_data, f, indent=2)
            self.master.set_option_states()

        self.close_geometry_dialog()

    @log_call
    def close_geometry_dialog(self, event=None):
        self.save_widget_geom_geometry()
        log.log_debug(log_text='Geometry dialog closing.')
        self.destroy()

    @log_call
    def restore_geom_geometry(self):
        """Restore window geometry of the Widget Geometry dialog from auto-saved preferences"""
        saved_geometry = pref.preference_setting(db_file_path=DB_FILE_PATH,
                                                 scope='window_geometry',
                                                 preference_name='widget_geometry')
        # self.geometry(saved_geometry)

    @log_call
    def save_widget_geom_geometry(self):
        """Save the widget geometry dialog's geometry to the repo, for the next time the dialog is launched."""
        geometry_row = pref.preference_row(db_file_path=DB_FILE_PATH,
                                           scope='window_geometry',
                                           preference_name='widget_geometry')
        panel_geometry = self.geometry()
        geometry_row["preference_value"] = panel_geometry
        pref.upsert_preference(db_file_path=DB_FILE_PATH, preference_row_dict=geometry_row)
