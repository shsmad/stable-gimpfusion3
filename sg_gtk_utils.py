import gi

gi.require_version("GimpUi", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import GimpUi, Gtk


def set_visibility_of(elements, visible=True):
    for element in elements:
        if visible:
            element.show()
        else:
            element.hide()

def add_textarea_to_container(procedure, config, argument_name, container):
    prompt_w = Gtk.TextView.new_with_buffer(GimpUi.prop_text_buffer_new(config, argument_name, 0))
    prompt_w.set_wrap_mode(Gtk.WrapMode.WORD)
    label = Gtk.Label(procedure.find_argument(argument_name).nick)
    label.set_halign(Gtk.Align.START)
    container.add(label)
    label.show()

    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.add(prompt_w)
    scrolled_window.set_min_content_height(75)

    container.add(scrolled_window)
    scrolled_window.show_all()

def set_toggle_control_by(checkbox_container, elements):
    def set_toggle(cb):
        for element in elements:
            element.set_sensitive(cb.get_active())

    checkbox = checkbox_container.get_children()[0]
    checkbox.connect("toggled", set_toggle)

def set_visibility_control_by(checkbox_container, elements):
    checkbox = checkbox_container.get_children()[0]
    checkbox.connect("toggled", lambda cb: set_visibility_of(elements, cb.get_active()))
