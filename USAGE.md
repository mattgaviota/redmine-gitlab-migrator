Redmine to Gitlab migrator
==========================

Proceso de Migration
--------------------

Este proceso se debe realizar por proyecto. **El Orden Importa**

### Crear el proyecto en Gitlab

No es necesario que tengan el mismo nombre. Solo hace falta su URL (eg:
*https://gitlab.salta.gob.ar/spys/sroyectos*).

### Crear usuarios

Los miembros del proyecto en gitlab necesitan tener los mismos nombres de
usuario que los miembros en redmine. Todos los miembros que interactuen con el
proyecto en Redmine deben ser agregados en el proyecto correspondiente en
Gitlab.

Si un usuario no se encuentra en gitlab, se te avisara de que  usuarios son
los que faltan.

### Chequear el proyecto en Redmine

Para un correcto funcionamiento, se debe agregar el estado **Migrado** al
proyecto. Y configurar que todos los tipos de peticiones puedan pasar de los
otros estados al estado migrado.

### Migrar las versiones

Si usas versiones, las *versiones* de Redmine se convertiran en *milestones*
de Gitlab. Si no se usan, se puede saltar este paso.

    migrate-rg roadmap --redmine-key xxxx --gitlab-key xxxx \
      https://redmine.example.com/projects/myproject \
      http://git.example.com/mygroup/myproject --check

*(eliminar el `--check` para realizar el comando, lo mismo para los demás)*

### Migrar peticiones

    migrate-rg issues --redmine-key xxxx --gitlab-key xxxx \
      https://redmine.example.com/projects/myproject \
      http://git.example.com/mygroup/myproject --check

Esto sirve para migrar las peticiones *Nuevas*. En caso de querer migrar las
peticiones *Cerradas* se debe usar

    migrate-rg issues --redmine-key xxxx --gitlab-key xxxx \
      https://redmine.example.com/projects/myproject \
      http://git.example.com/mygroup/myproject --closed --check

Nota. Esto **no** mantendrá los ID originales de Redmine.
