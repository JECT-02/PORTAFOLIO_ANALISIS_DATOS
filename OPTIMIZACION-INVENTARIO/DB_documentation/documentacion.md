# Documentación del Dataset: `thelook_ecommerce`

## Resumen General

Este dataset simula una tienda de ropa online (TheLook) creado por Looker. 
Contiene **8 tablas** relacionales con datos de clientes, órdenes, 
productos, inventario, eventos web y centros de distribución. 
Es ideal para análisis de cohortes, funnel de conversión, segmentación de clientes 
y análisis de revenue por canal.

## Tablas y Estructura de Columnas

### `distribution_centers`

| Columna | Tipo | Modo | Descripción |
|:---|:---|:---|:---|
| `id` | INTEGER | NULLABLE | Identificador único del centro de distribución |
| `name` | STRING | NULLABLE | Nombre de la ciudad/sede del centro de distribución |
| `latitude` | FLOAT | NULLABLE | Latitud geográfica del centro |
| `longitude` | FLOAT | NULLABLE | Longitud geográfica del centro |
| `distribution_center_geom` | GEOGRAPHY | NULLABLE | — |

### `events`

| Columna | Tipo | Modo | Descripción |
|:---|:---|:---|:---|
| `id` | INTEGER | NULLABLE | Identificador único del evento web |
| `user_id` | INTEGER | NULLABLE | Referencia al usuario que generó el evento |
| `sequence_number` | INTEGER | NULLABLE | Número de secuencia del evento dentro de la sesión |
| `session_id` | STRING | NULLABLE | Identificador de la sesión de navegación |
| `created_at` | TIMESTAMP | NULLABLE | Fecha y hora en que ocurrió el evento |
| `ip_address` | STRING | NULLABLE | Dirección IP del usuario |
| `city` | STRING | NULLABLE | Ciudad desde donde se generó el evento |
| `state` | STRING | NULLABLE | Estado o región |
| `postal_code` | STRING | NULLABLE | Código postal |
| `browser` | STRING | NULLABLE | Navegador web utilizado |
| `traffic_source` | STRING | NULLABLE | Canal de adquisición (Organic, Facebook, Email, etc.) |
| `uri` | STRING | NULLABLE | Página o recurso visitado |
| `event_type` | STRING | NULLABLE | Tipo de evento: product, cart, purchase, department, home |

### `inventory_items`

| Columna | Tipo | Modo | Descripción |
|:---|:---|:---|:---|
| `id` | INTEGER | NULLABLE | Identificador único del ítem en inventario |
| `product_id` | INTEGER | NULLABLE | Referencia al producto en el catálogo |
| `created_at` | TIMESTAMP | NULLABLE | Fecha de ingreso al inventario |
| `sold_at` | TIMESTAMP | NULLABLE | Fecha de venta (NULL si aún no se vendió) |
| `cost` | FLOAT | NULLABLE | Costo del producto para la empresa |
| `product_category` | STRING | NULLABLE | Categoría del producto |
| `product_name` | STRING | NULLABLE | Nombre del producto |
| `product_brand` | STRING | NULLABLE | Marca del producto |
| `product_retail_price` | FLOAT | NULLABLE | Precio de venta al público |
| `product_department` | STRING | NULLABLE | Departamento (Men, Women) |
| `product_sku` | STRING | NULLABLE | Código SKU del producto |
| `product_distribution_center_id` | INTEGER | NULLABLE | Centro de distribución donde está ubicado |

### `order_items`

| Columna | Tipo | Modo | Descripción |
|:---|:---|:---|:---|
| `id` | INTEGER | NULLABLE | Identificador único de la línea de orden |
| `order_id` | INTEGER | NULLABLE | Referencia a la orden padre |
| `user_id` | INTEGER | NULLABLE | Referencia al cliente que compró |
| `product_id` | INTEGER | NULLABLE | Referencia al producto comprado |
| `inventory_item_id` | INTEGER | NULLABLE | Referencia al ítem específico del inventario |
| `status` | STRING | NULLABLE | Estado: Complete, Shipped, Processing, Cancelled, Returned |
| `created_at` | TIMESTAMP | NULLABLE | Fecha de creación de la línea |
| `shipped_at` | TIMESTAMP | NULLABLE | Fecha de envío |
| `delivered_at` | TIMESTAMP | NULLABLE | Fecha de entrega |
| `returned_at` | TIMESTAMP | NULLABLE | Fecha de devolución (si aplica) |
| `sale_price` | FLOAT | NULLABLE | Precio final de venta (puede incluir descuentos) |

### `orders`

| Columna | Tipo | Modo | Descripción |
|:---|:---|:---|:---|
| `order_id` | INTEGER | NULLABLE | Identificador único de la orden |
| `user_id` | INTEGER | NULLABLE | Referencia al cliente |
| `status` | STRING | NULLABLE | Estado general de la orden |
| `gender` | STRING | NULLABLE | Género del usuario (registrado en la orden) |
| `created_at` | TIMESTAMP | NULLABLE | Fecha de creación de la orden |
| `returned_at` | TIMESTAMP | NULLABLE | Fecha de devolución total (si aplica) |
| `shipped_at` | TIMESTAMP | NULLABLE | Fecha de envío de la orden |
| `delivered_at` | TIMESTAMP | NULLABLE | Fecha de entrega de la orden |
| `num_of_item` | INTEGER | NULLABLE | Cantidad total de ítems en la orden |

### `products`

| Columna | Tipo | Modo | Descripción |
|:---|:---|:---|:---|
| `id` | INTEGER | NULLABLE | Identificador único del producto |
| `cost` | FLOAT | NULLABLE | Costo base del producto |
| `category` | STRING | NULLABLE | Categoría (ej: Accessories, Tops, Swim, etc.) |
| `name` | STRING | NULLABLE | Nombre del producto |
| `brand` | STRING | NULLABLE | Marca |
| `retail_price` | FLOAT | NULLABLE | Precio sugerido de venta al público |
| `department` | STRING | NULLABLE | Departamento (Men o Women) |
| `sku` | STRING | NULLABLE | Código SKU único |
| `distribution_center_id` | INTEGER | NULLABLE | Centro de distribución principal |

### `thelook_ecommerce-table`

| Columna | Tipo | Modo | Descripción |
|:---|:---|:---|:---|

### `users`

| Columna | Tipo | Modo | Descripción |
|:---|:---|:---|:---|
| `id` | INTEGER | NULLABLE | Identificador único del cliente |
| `first_name` | STRING | NULLABLE | Nombre |
| `last_name` | STRING | NULLABLE | Apellido |
| `email` | STRING | NULLABLE | Correo electrónico |
| `age` | INTEGER | NULLABLE | Edad |
| `gender` | STRING | NULLABLE | Género (M/F) |
| `state` | STRING | NULLABLE | Estado o provincia |
| `street_address` | STRING | NULLABLE | Dirección |
| `postal_code` | STRING | NULLABLE | Código postal |
| `city` | STRING | NULLABLE | Ciudad |
| `country` | STRING | NULLABLE | País |
| `latitude` | FLOAT | NULLABLE | Latitud de la dirección |
| `longitude` | FLOAT | NULLABLE | Longitud de la dirección |
| `traffic_source` | STRING | NULLABLE | Canal por el que llegó el usuario (Organic, Facebook, etc.) |
| `created_at` | TIMESTAMP | NULLABLE | Fecha de registro del usuario |
| `user_geom` | GEOGRAPHY | NULLABLE | — |

## Relaciones entre Tablas (PK / FK)

A continuación se detallan las relaciones lógicas entre tablas basadas en 
el diseño del dataset y los nombres de columnas:

| Relación | Descripción |
|:---|:---|
| `users.id` → PK | Identificador único del cliente |
| `users.id` ← `orders.user_id` | Un usuario puede tener múltiples órdenes |
| `users.id` ← `events.user_id` | Un usuario genera múltiples eventos web |
| `users.id` ← `order_items.user_id` | Redundancia desnormalizada en líneas de orden |
| `orders.order_id` → PK | Identificador único de la orden |
| `orders.order_id` ← `order_items.order_id` | Una orden contiene múltiples líneas |
| `products.id` → PK | Identificador único del producto en catálogo |
| `products.id` ← `inventory_items.product_id` | Un producto tiene múltiples unidades en inventario |
| `products.id` ← `order_items.product_id` | Un producto puede aparecer en muchas órdenes |
| `inventory_items.id` → PK | Identificador único de la unidad en inventario |
| `inventory_items.id` ← `order_items.inventory_item_id` | Cada línea de orden apunta a una unidad específica |
| `distribution_centers.id` → PK | Identificador único del centro de distribución |
| `distribution_centers.id` ← `inventory_items.product_distribution_center_id` | Inventario ubicado en un centro |
| `distribution_centers.id` ← `products.distribution_center_id` | Producto asignado a un centro |

## Notas para el Análisis

- **Eventos (`events`)**: Contiene ~2.4M registros de comportamiento web. 
Útil para construir funnels de conversión (product → cart → purchase).

- **Órdenes (`orders`) vs Líneas (`order_items`)**: Modelo cabecera-detalle. 
Una orden puede tener múltiples líneas. El precio final está en `order_items.sale_price`.

- **Inventario (`inventory_items`)**: Registro a nivel de unidad física. 
`sold_at` es NULL hasta que se vende. Permite análisis de rotación.

- **Usuarios (`users`)**: Tabla de dimensiones del cliente. Incluye geolocalización 
y canal de adquisición (`traffic_source`).

- **Desnormalización**: Algunas tablas repiten `user_id` o `product_id` para facilitar 
consultas directas sin joins obligatorios.
