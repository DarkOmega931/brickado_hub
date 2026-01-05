Brickado Hub - Pacote de UI Dark Neon
=====================================

Este pacote contém:

- templates/base.html   (layout principal dark)
- templates/core/home.html
- static/css/brickado.css
- static/img/brickado-logo.png
- requirements.txt (dependências principais)

Como usar
---------

1. Copie o conteúdo de `templates/` para o diretório de templates do seu projeto Django.
2. Copie `static/` para a pasta de estáticos do projeto (`STATICFILES_DIRS`).
3. Certifique-se de que o app `core` usa `core/home.html` na view `home`.
4. Rode `python manage.py collectstatic` quando estiver preparando o deploy.