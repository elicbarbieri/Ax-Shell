import gi
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.scale import Scale
from fabric.widgets.button import Button
from fabric.widgets.image import Image
from fabric.widgets.scrolledwindow import ScrolledWindow
from services.audio import AudioService

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

import config.data as data

vertical_mode = (
    True
    if data.PANEL_THEME == "Panel"
    and (
        data.BAR_POSITION in ["Left", "Right"]
        or data.PANEL_POSITION in ["Start", "End"]
    )
    else False
)


class DeviceSelector(Box):
    """Device selector dropdown for output/input devices"""
    
    def __init__(self, audio_service: AudioService, device_type: str):
        super().__init__(orientation="h", spacing=8)
        self.audio_service = audio_service
        self.device_type = device_type  # "sink" or "source"
        
        self.label = Label(f"{device_type.title()}:")
        self.combo = Gtk.ComboBoxText()
        self.combo.connect("changed", self._on_changed)
        
        self.add(self.label)
        self.add(self.combo)
        self.update()

    def update(self):
        """Refresh device list"""
        self.combo.remove_all()
        
        if self.device_type == "sink":
            devices = self.audio_service.get_sinks()
        else:
            devices = self.audio_service.get_sources()
        
        for device in devices:
            node_id = device.get_bound_id()
            name = self.audio_service.get_node_name(node_id)
            device_type = self.audio_service.get_device_type(node_id)
            display_name = f"{name} ({device_type})"
            self.combo.append(str(node_id), display_name)

    def _on_changed(self, combo):
        """Device selected"""
        active_id = combo.get_active_id()
        if not active_id:
            return
            
        node_id = int(active_id)
        if self.device_type == "sink":
            self.audio_service.set_default_sink(node_id)
        else:
            self.audio_service.set_default_source(node_id)


class VolumeSlider(Box):
    """Volume control with icon, name, slider, mute button, and percentage"""
    
    def __init__(self, audio_service: AudioService, node_id: int):
        super().__init__(orientation="h", spacing=8)
        self.audio_service = audio_service
        self.node_id = node_id
        self._updating = False
        
        # Icon
        icon_name = self.audio_service.get_icon_name(node_id)
        self.icon = Image.new_from_icon_name(icon_name, Gtk.IconSize.SMALL_TOOLBAR)
        
        # Name label
        name = self.audio_service.get_node_name(node_id)
        self.name_label = Label(name)
        self.name_label.set_ellipsize(3)  # ELLIPSIZE_END
        self.name_label.set_max_width_chars(25)
        
        # Volume slider
        current_volume = self.audio_service.get_volume(node_id) or 0.0
        self.volume_slider = Scale(
            orientation="h",
            range=(0.0, 1.0),
            value=current_volume,
            h_expand=True
        )
        self.volume_slider.connect("value-changed", self._on_volume_changed)
        
        # Mute button
        is_muted = self.audio_service.get_mute_state(node_id) or False
        self.mute_button = Button("🔇" if is_muted else "🔊")
        self.mute_button.connect("clicked", self._on_mute_clicked)
        
        # Volume percentage label
        percentage = int(current_volume * 100)
        self.volume_label = Label(f"{percentage}%")
        self.volume_label.set_size_request(40, -1)
        
        # Layout
        self.add(self.icon)
        self.add(self.name_label)
        self.add(self.volume_slider)
        self.add(self.mute_button)
        self.add(self.volume_label)
        
        # Apply muted style if needed
        self._update_muted_style()

    def _on_volume_changed(self, scale):
        """Volume slider moved"""
        if self._updating:
            return
            
        volume = scale.get_value()
        self.audio_service.set_volume(self.node_id, volume)
        
        # Update percentage label
        percentage = int(volume * 100)
        self.volume_label.set_text(f"{percentage}%")

    def _on_mute_clicked(self, button):
        """Mute button clicked"""
        current_mute = self.audio_service.get_mute_state(self.node_id) or False
        new_mute = not current_mute
        
        self.audio_service.set_mute(self.node_id, new_mute)
        button.set_label("🔇" if new_mute else "🔊")
        self._update_muted_style()

    def _update_muted_style(self):
        """Update visual style based on mute state"""
        is_muted = self.audio_service.get_mute_state(self.node_id) or False
        if is_muted:
            self.add_style_class("muted")
        else:
            self.remove_style_class("muted")

    def update(self):
        """Refresh from audio service"""
        self._updating = True
        
        # Update volume slider
        volume = self.audio_service.get_volume(self.node_id) or 0.0
        self.volume_slider.set_value(volume)
        
        # Update percentage label
        percentage = int(volume * 100)
        self.volume_label.set_text(f"{percentage}%")
        
        # Update mute button
        is_muted = self.audio_service.get_mute_state(self.node_id) or False
        self.mute_button.set_label("🔇" if is_muted else "🔊")
        self._update_muted_style()
        
        self._updating = False


class MixerSection(Box):
    """Container for device + stream controls"""
    
    def __init__(self, audio_service: AudioService, section_type: str):
        super().__init__(orientation="v", spacing=4)
        self.audio_service = audio_service
        self.section_type = section_type  # "output" or "input"
        
        # Title
        self.title = Label(f"{section_type.title()} Devices & Streams")
        self.title.set_markup(f"<b>{section_type.title()} Devices & Streams</b>")
        self.add(self.title)
        
        # Container for sliders
        self.sliders_box = Box(orientation="v", spacing=4)
        self.add(self.sliders_box)

    def update(self):
        """Refresh all sliders"""
        # Clear existing sliders
        for child in self.sliders_box.get_children():
            self.sliders_box.remove(child)
        
        # Get nodes for this section
        if self.section_type == "output":
            devices = self.audio_service.get_sinks()
            streams = self.audio_service.get_sink_inputs()
        else:
            devices = self.audio_service.get_sources()
            streams = self.audio_service.get_source_outputs()
        
        # Add device sliders first
        for device in devices:
            node_id = device.get_bound_id()
            slider = VolumeSlider(self.audio_service, node_id)
            self.sliders_box.add(slider)
        
        # Add stream sliders
        for stream in streams:
            node_id = stream.get_bound_id()
            slider = VolumeSlider(self.audio_service, node_id)
            self.sliders_box.add(slider)
        
        self.show_all()


class Mixer(Box):
    """Main mixer container with device selectors and volume controls"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="mixer",
            orientation="v",
            spacing=12,
            h_expand=True,
            v_expand=True
        )
        
        # Initialize AudioService
        try:
            self.audio_service = AudioService()
        except Exception as e:
            error_label = Label(
                label=f"AudioService unavailable: {str(e)}",
                h_align="center",
                v_align="center",
                h_expand=True,
                v_expand=True,
            )
            self.add(error_label)
            return
        
        # Device selectors at top
        self.device_selectors = Box(orientation="h", spacing=16)
        self.output_selector = DeviceSelector(self.audio_service, "sink")
        self.input_selector = DeviceSelector(self.audio_service, "source")
        
        self.device_selectors.add(self.output_selector)
        self.device_selectors.add(self.input_selector)
        
        # Mixer sections in scrollable area
        self.mixer_scroll = ScrolledWindow(
            h_expand=True,
            v_expand=True
        )
        
        self.mixer_content = Box(
            orientation="h" if not vertical_mode else "v",
            spacing=16,
            h_expand=True,
            v_expand=True
        )
        
        self.output_section = MixerSection(self.audio_service, "output")
        self.input_section = MixerSection(self.audio_service, "input")
        
        self.mixer_content.add(self.output_section)
        self.mixer_content.add(self.input_section)
        self.mixer_scroll.add(self.mixer_content)
        
        # Layout
        self.add(self.device_selectors)
        self.add(self.mixer_scroll)
        
        # Connect to audio service signals
        self.audio_service.connect("devices-changed", self._on_audio_changed)
        self.audio_service.connect("streams-changed", self._on_audio_changed)
        self.audio_service.connect("volume-changed", self._on_volume_changed)
        
        # Initial update with delay for WirePlumber connection
        GLib.timeout_add(500, self._initial_update)

    def _initial_update(self):
        """Initial update after WirePlumber connection"""
        self.update_all()
        return False  # Don't repeat

    def _on_audio_changed(self, *args):
        """Audio devices or streams changed"""
        self.update_all()

    def _on_volume_changed(self, service, node_id, volume, is_muted):
        """Volume changed - update specific slider if visible"""
        # For now, just do a full update
        # TODO: Optimize to update only the specific slider
        pass

    def update_all(self):
        """Update entire mixer UI"""
        if not hasattr(self, 'audio_service'):
            return
            
        # Update device selectors
        self.output_selector.update()
        self.input_selector.update()
        
        # Update mixer sections
        self.output_section.update()
        self.input_section.update()