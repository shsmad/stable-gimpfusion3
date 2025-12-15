xgettext -k_ -kgettext_lazy -kN_ -o locale/stable-gimpfusion3.pot \
--from-code=UTF-8 --package-name=stable-gimpfusion3 --package-version=0.1.0 \
--language=Python --copyright-holder=shsmad --add-comments=TRANSLATORS \
stable-gimpfusion3.py sg_constants.py sg_plugins/*.py sg_proc_arguments.py sg_structures.py sg_utils.py

# msginit -l ru -i locale/stable-gimpfusion3.pot -o locale/ru/LC_MESSAGES/stable-gimpfusion3.po

# Обновить все переводы
for lang in ru en; do
  if [ -f "locale/${lang}/LC_MESSAGES/stable-gimpfusion3.po" ]; then
    msgmerge -U "locale/${lang}/LC_MESSAGES/stable-gimpfusion3.po" locale/stable-gimpfusion3.pot
    msgfmt "locale/${lang}/LC_MESSAGES/stable-gimpfusion3.po" \
      -o "locale/${lang}/LC_MESSAGES/stable-gimpfusion3.mo"
  fi
done
