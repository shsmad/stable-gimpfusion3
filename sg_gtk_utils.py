import gi

gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import GimpUi, Gtk


def add_textarea_to_container(procedure, config, argument_name, container):
    prompt_w = Gtk.TextView.new_with_buffer(GimpUi.prop_text_buffer_new(config, argument_name, 0))
    prompt_w.set_wrap_mode(Gtk.WrapMode.WORD)
    label = Gtk.Label(procedure.find_argument(argument_name).nick)
    label.set_halign(Gtk.Align.START)
    container.add(label)
    label.show()
    container.add(prompt_w)
    prompt_w.show()
