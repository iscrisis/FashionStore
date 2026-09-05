"""Paquete funcional P2 — Usuarios y accesos.

Agrupa los casos de uso relacionados con la identidad de los usuarios del sistema:

- CU01 — Iniciar sesión (implementado)
- CU02 — Registrar cliente (pendiente)
- CU03 — Recuperar contraseña (pendiente)
- CU04 — Actualizar perfil (pendiente)
- CU05 — Gestionar usuarios y roles (pendiente)

``Models/`` contiene las entidades compartidas por todos los CU de este paquete
(Usuario, Rol). Cada ``CUxx_.../`` contiene únicamente la lógica exclusiva de
ese caso de uso (router, schemas, service, repository).
"""
