from __future__ import annotations

import gi

gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gimp, GimpUi, Gio, GLib, Gtk

from sg_i18n import _


def set_visibility_of(elements: list[Gtk.Widget], visible: bool = True) -> None:
    for element in elements:
        if visible:
            element.show()
        else:
            element.hide()


def add_textarea_to_container(
    procedure: Gimp.Procedure,
    config: Gimp.ProcedureConfig,
    argument_name: str,
    container: Gtk.Container,
) -> None:
    prompt_w = Gtk.TextView.new_with_buffer(GimpUi.prop_text_buffer_new(config, argument_name, 0))
    prompt_w.set_wrap_mode(Gtk.WrapMode.WORD)
    label = Gtk.Label(_(procedure.find_argument(argument_name).nick))
    label.set_halign(Gtk.Align.START)
    container.add(label)
    label.show()

    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.add(prompt_w)
    scrolled_window.set_min_content_height(75)

    container.add(scrolled_window)
    scrolled_window.show_all()


def set_toggle_control_by(checkbox_container: Gtk.Container, elements: list[Gtk.Widget]) -> None:
    def set_toggle(cb: Gtk.ToggleButton) -> None:
        for element in elements:
            element.set_sensitive(cb.get_active())

    checkbox = checkbox_container.get_children()[0]
    checkbox.connect("toggled", set_toggle)


def set_visibility_control_by(checkbox_container: Gtk.Container, elements: list[Gtk.Widget]) -> None:
    checkbox = checkbox_container.get_children()[0]
    checkbox.connect("toggled", lambda cb: set_visibility_of(elements, cb.get_active()))


class MemFile:
    def __init__(self, filepath: str) -> None:
        self.stream = Gio.MemoryOutputStream.new_resizable()
        self.bytes_written = 0
        self.filepath = filepath

    def write(self, data):
        """
        Writes binary data to the memory stream.
        """
        data_bytes = GLib.Bytes.new_take(data)
        written = self.stream.write_bytes(data_bytes)
        self.bytes_written += written
        return written

    def seek(self, offset, whence=GLib.SeekType.SET):
        """
        Seek to a specific position in the stream.
        """
        self.stream.seek(offset, whence)

    def tell(self):
        """
        Return the current position in the stream.
        """
        return self.stream.tell()

    def close(self):
        """
        Closes the stream.
        """
        self.stream.close()

    def flush(self):
        """
        Flush the internal buffer.
        """
        self.stream.flush()

    def read(self, size=-1):
        """
        Reads data from the stream.
        """
        # Convert MemoryOutputStream back to MemoryInputStream for reading
        mem_input_stream = Gio.MemoryInputStream.new_from_bytes(self.stream.steal_as_bytes())
        buf = bytearray(size)
        read_len = mem_input_stream.read(buf)
        return bytes(buf[:read_len])

    def truncate(self, size=None):
        """
        Truncate the stream to a specific size.
        """
        if size is None:
            size = self.tell()
        self.stream.truncate(size)

    def getvalue(self):
        """
        Retrieve the entire contents of the stream.
        """
        return self.stream.steal_as_bytes().get_data()
