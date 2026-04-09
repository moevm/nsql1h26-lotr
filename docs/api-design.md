# API Design Document
* Стек: Django, DRF, Neo4j, React, Pytest
* Может быть будет: 
* * Pydantic (надо посмотреть насколько она нам нужен вообще/сейчас, насколько сложно его будет впихнуть потом)
* * Allure (впихнём потом, когда будем заниматься тестированием, если будет время)

### Контекст, принципы, замечания

* API-first подход: сначала согласовываем контракт, потом генерится OpenAPI-схемка (`spectacular`, не `yasg` - он вроде устарел), и только потом пишется код. Фронт пашет на MSW-моках или моках в `src/mocks/handlers.ts`, бэкенда не ждёт. Этот файлик нужен только на первых порах - чтобы обговорить и обдумать. Дальше смотрим только на схемку OpenAPI.

* slug как публичный идентификатор. Внутренние id из Neo4j не покидают бэкенд, так как они могут меняться и всё такое. Во всех URL используются слаги.

* Аутентификация через JWT. Я погуглил, и в нашем случае в сессионной будет больше танцев.

* Ролей пока будет две: `viewer` (чтение почти всего, лайки, комменты) и `admin` (+ создание/редактирование/удаление сущностей, import/export). Роль хранится в Neo4j-ноде пользователя и возвращается в `GET /auth/me`. Фронт по роли показывает/скрывает UI элементы. Бэк проверяет роль в каждом защищённом эндпоинте независимо (для надёжности)

* Для разработки демо будут debug-пользователи, по одному на каждую роль. Будут создаваться какой-нибудь seed-командой при первом запуске.

### Общее по всем эндпоинтам

#### Base URL: 
```
/api/v1
```
v1 это не версия приложения, а версия контракта API. Зачем это нужно и почему так делают почитайте в инете

#### Заголовки:
```
Content-Type:  application/json
Authorization: Bearer <access_token>    # для защищённых эндпоинтов
```

#### Пагинация:

Все списки пагинированы. Параметры:
```
?page=1             # номер страницы, default: 1
?page_size=20       # размер страницы, default: 20, max: 100
```
#### Формат ответа всегда:
```
{
  "count":    150,
  "next":     "/api/v1/.../?page=2&page_size=20",
  "previous": null,
  "results":  [ ... ]
}
```
`next` и `previous` - полные URL со всеми query параметрами. Фронт вручную URL пагинацию не делает.

#### Сортировка:
```
?sort=name&order=asc    # order: asc | desc, default: asc
```
Допустимые значения `sort` описаны в каждом каталоге отдельно

#### Текстовые фильтры:

Все текстовые фильтры регистронезависимые, по подстроке (`CONTAINS` или что-то такое)

#### Формат ошибок:

Единый для всех эндпоинтов:
```
{
  "error": {
    "code":    "VALIDATION_ERROR",
    "message": "Human-readable description in English",
    "fields":  {
      "names":  ["This field is required."],
      "gender": ["Must be one of: male, female, unknown."]
    }
  }
}
```
`fields` = `null` если ошибка не связана с конкретными полями

## Собственно эндпоинты

### Аутентификация и авторизация

#### `POST /api/v1/auth/register`

Регистрация нового пользователя. После успешной регистрации пользователь автоматически авторизован.

Запрос:
```
{
  "username":         "bilbo_baggins",
  "email":            "bilbo@shire.me",
  "password":         "bebsigola",
  "password_confirm": "bebsigola"   # Этого поля может не быть, мб будем проверять на фронте, пока не знаю
}
```

Ответ 201:
```
{
  "user": {
    "username":  "bilbo_baggins",
    "email": "bilbo@shire.me",
    "role": "viewer",
    "avatarUrl": null,
    "createdAt": "2022-02-02T00:00:00Z"
  },
  "tokens": {
    "access":  "eyJ...",
    "refresh": "eyJ..."
  }
}
```

Ответ 400 - невалидные данные:
```
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "fields": {
      "username": ["A user with this username already exists."],
      "password": ["Password must be at least 8 characters."]
    }
  }
}
```

#### `POST /api/v1/auth/login` 

Логин существующего пользователя.

Запрос:
```
{
  "username": "bilbo_baggins",
  "password": "MyPrecious1!"
}
```

Ответ 200:
```
{
  "user": {
    "username":  "bilbo_baggins",
    "email": "bilbo@shire.me",
    "role": "viewer", // "viewer" | "admin"
    "avatarUrl": null,
    "createdAt": "2024-01-01T00:00:00Z"
  },
  "tokens": {
    "access": "abc...",
    "refresh": "abs...",
  }
}
```

Ответ 401:
```
{
  "error": {
    "code":    "INVALID_CREDENTIALS",
    "message": "Invalid username or password.",
    "fields":  null
  }
}
```

#### `POST /api/v1/auth/refresh/`

Запрос:
```
{ "refresh": "abs..." }
```

Ответ:
```
{ "refresh": "abs..." }
```

Ответ 401 - токен истёк или в blacklist:
```
{
  "error": {
    "code":    "TOKEN_EXPIRED",
    "message": "Refresh token is expired or invalid.",
    "fields":  null
  }
}
```

#### `POST /api/v1/auth/logout/`

Пользователь выходит из профиля.  Инвалидирует refresh token на бэкенде.

Запрос:
```
{ "refresh": "eyJ..." }
```

Ответ 204:
```
{} // Пустой
```

#### `GET /api/v1/auth/me/`

Требует авторизации. Показывает пользователю его страницу.

Ответ 200:
```
{
  "username":  "bilbo_baggins",
  "email": "bilbo@shire.me",
  "role": "viewer",
  "avatarUrl": "https://cdn.example.com/avatars/bilbo.jpg",
  "createdAt": "2022-02-02T00:00:00Z",
  "likedPages": [
    { "slug": "frodo-baggins", "name": "Frodo Baggins", "type": "character" },
    { "slug": "the-shire",     "name": "The Shire",     "type": "location"  }
  ]
}
```

#### `PATCH /api/v1/auth/me/`

Требует авторизации. Все поля опциональны. При смене пароля `password_current` обязателен.

Запрос:
```
{
  "username":         "bilbo_old_baggins",
  "email":            "newbilbo@shire.me",
  "avatarUrl":        "https://cdn.example.com/avatars/bilbo2.jpg",
  "password":         "NewPrecious1!",
  "password_current": "MyPrecious1!"
}
```

Ответ 200:

Новый объект пользователя, как `GET /.../me`

Ответ 400:
```
{
  "error": {
    "code":    "VALIDATION_ERROR",
    "message": "Invalid input",
    "fields": {
      "password_current": ["Current password is incorrect."],
      "email": ["A user with this email already exists."]
    }
  }
}
```

### Pages

Все сущности чита.тся и редактируются через единый `/pages/{slug}`. Создание - через типизированные каталоги (дальше будет)
```
GET    /api/v1/pages/{slug}/
PATCH  /api/v1/pages/{slug}/
DELETE /api/v1/pages/{slug}/
POST   /api/v1/pages/{slug}/like/
DELETE /api/v1/pages/{slug}/like/
GET    /api/v1/pages/{slug}/comments/
POST   /api/v1/pages/{slug}/comments/
GET    /api/v1/pages/{slug}/export/
POST   /api/v1/pages/{slug}/import/
```

#### `GET /api/v1/pages/{slug}/` 

Публичный. `isLiked` - `null` если пользователь не авторизован, при нажатии на лайк переводит на регистрацию, иначе - булево значение.

Надо выбрать из двух:
1. Все type-specific поля присутствуют в ответе всегда. Для данного типа они заполнены, для остальных - `null`. Это позволяет фронту иметь единый TypeScript-тип и не делать type narrowing при чтении ответа, но раздувает ответ. Мб это херня решение, но надо погуглить.
2. Type-specific ответы. Вроде по феншую, но по коду сложнее. Гуглим ребята, гуглим.

Ответ 200:
```
1.
{
  "slug": "frodo-baggins",
  "type": "character",
  "names": ["Frodo Baggins", "Mr. Underhill", "Ring-bearer"],

  // Character fields
  "titles":    ["Ring-bearer"],
  "gender":    "male",
  "birthDate": "TA 2968",
  "deathDate": "FO 61",
  "hair":      "brown, curly",
  "eyes":      "blue",
  "height":    "3 feet 6 inches",
  "weapon":    "Sting, Barrow-blade",
  "clothing":  "Hobbit clothes, mithril coat",
  "notableFor": "Destroyed the One Ring at Mount Doom",

  // Race fields
  "lifespan":     null,
  "avgHeight":    null,
  "skin":         null,
  "distinctions": null,

  // Location fields
  "locationType":    null,
  "population":      null,
  "creationDate":    null,
  "destructionDate": null,

  // Event fields
  "eventType":  null,
  "startDate":  null,
  "endDate":    null,
  "casualties": null,

  // Organization fields
  "orgType":       null,
  "foundedDate":   null,
  "dissolvedDate": null,
  "purpose":       null,
  "weaponry":      null,

  // Timeline fields
  "abbreviation": null,

  // Item fields
  "itemType": null,
  "material": null,

  // Language fields
  "family": null,

  // Article — null если статья ещё не создана
  "article": {
    "text":      "Frodo Baggins was a hobbit of the Shire...",
    "imageUrl":  "https://cdn.example.com/frodo.jpg",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-03-15T12:30:00Z"
  },

  // Связи - ключ = тип ребра в Neo4j
  // Возвращаются все известные типы рёбер, пустые - как []
  // Фронт рендерит только непустые
  "relations": { ... },

  "categories": [
    { "slug": "hobbits-of-the-shire", "name": "Hobbits of the Shire" },
    { "slug": "fellowship-members",   "name": "Fellowship Members" }
  ],

  "likesCount":    42,
  "isLiked":       true,
  "commentsCount": 7
}

2.
{
  "slug": "frodo",
  "type": "character", // discriminator
  "names": ["Frodo"],
  "attributes": {
    "gender": "male",
    "weapon": "Sting"
    // ... only character fields
  },
  "relations": { ... }
}
```

Для связей тоже есть два варианта:
```
1.
"relations": {
    "BELONGS_TO_RACE": [
      { "slug": "hobbits", "type": "race", "name": "Hobbits", "imageUrl": null }
    ],
    "MEMBER_OF": [
      { "slug": "fellowship-of-the-ring", "type": "organization", "name": "Fellowship of the Ring", "imageUrl": "..." }
    ],
    "PARTICIPATED_IN": [
      { "slug": "war-of-the-ring",      "type": "event", "name": "War of the Ring",      "imageUrl": null },
      { "slug": "quest-of-mount-doom",  "type": "event", "name": "Quest of Mount Doom",  "imageUrl": null }
    ],
    "BORN_IN": [
      { "slug": "the-shire", "type": "location", "name": "The Shire", "imageUrl": "..." }
    ],
    "LIVED_IN": [
      { "slug": "bag-end",    "type": "location", "name": "Bag End",    "imageUrl": "..." },
      { "slug": "rivendell",  "type": "location", "name": "Rivendell",  "imageUrl": "..." }
    ],
    "OWNS": [
      { "slug": "the-one-ring", "type": "item", "name": "The One Ring", "imageUrl": "..." },
      { "slug": "sting",        "type": "item", "name": "Sting",        "imageUrl": "..." }
    ],
    "KNOWS":     [ { "slug": "samwise-gamgee", "type": "character", "name": "Samwise Gamgee", "imageUrl": "..." } ],
    "PARENT_OF": [],
    "CHILD_OF":  [ { "slug": "drogo-baggins",  "type": "character", "name": "Drogo Baggins",  "imageUrl": null } ],
    "SPEAKS":    [],
    "RULED_BY":  [],
    "LOCATED_IN":    [],
    "HAPPENED_IN":   [],
    "DURING":        [],
    "PART_OF":       []
  },

2.
"relationships": {
    "outgoing": [
    {
        "id": "rel_123", // Internal Neo4j ID или UUID
        "type": "OF_RACE",
        "target": {
        "slug": "hobbits",
        "type": "race",
        "name": "Hobbits"
        },
        "properties": {}
    },
    {
        "id": "rel_124",
        "type": "MEMBER_OF",
        "target": {
        "slug": "fellowship-of-the-ring",
        "type": "organization",
        "name": "Fellowship of the Ring"
        },
        "properties": {
        "role": "Ring-bearer",
        "from_date": "TA 3018",
        "to_date": "TA 3019"
        }
    },
    {
        "id": "rel_125",
        "type": "BORN_IN",
        "target": {
        "slug": "the-shire",
        "type": "location",
        "name": "The Shire"
        }
    }
    ],
    "incoming": [
    {
        "id": "rel_126",
        "type": "CHILD_OF",
        "from": {
        "slug": "bilbo-baggins",
        "type": "character",
        "name": "Bilbo Baggins"
        },
        "properties": {
        "type": "adoptive"
        }
    }
    ]
},

Комбинированный??:
"relations": {
  "outgoing": {
    "BELONGS_TO_RACE": [
      {
        "target": { "slug": "hobbits", "type": "race", "name": "Hobbits", "imageUrl": null },
        "properties": {}
      }
    ],
    "MEMBER_OF": [
      {
        "target": { "slug": "fellowship-of-the-ring", "type": "organization", "name": "Fellowship of the Ring" },
        "properties": {
          "role": "Ring-bearer",
          "from_date": "TA 3018",
          "to_date": "TA 3019"
        }
      }
    ],
    "BORN_IN": [
      {
        "target": { "slug": "the-shire", "type": "location", "name": "The Shire" },
        "properties": {}
      }
    ]
  },
  "incoming": {
    "CHILD_OF": [
      {
        "from": { "slug": "bilbo-baggins", "type": "character", "name": "Bilbo Baggins" },
        "properties": { "type": "adoptive" }
      }
    ]
  }
}
```

Вариантов много, надо обсудить.

Ответ 404:
```
{
  "error": {
    "code":    "NOT_FOUND",
    "message": "Page 'frodo-bagginss' does not exist.",
    "fields":  null
  }
}
```

#### `PATCH /api/v1/pages/{slug}/`

Требует роль `admin`. Принмает только изменяемые поля - патчу весь объект передавать странно. Для `relations`: передаётся полный список слагов для каждого типа ребра. Если типа ребра в запросе не указан, то он не изменяется. Если передан пустой массив - все рёбра этого типа удаляются.

Запрос:
```
{
  "names":     ["Frodo Baggins", "Mr. Underhill", "Ring-bearer", "Elf-friend"],
  "deathDate": "FO 61",
  "notableFor": "Destroyed the One Ring. Later sailed to Valinor.",
  "article": {
    "text":     "Updated article text...",
    "imageUrl": "https://cdn.example.com/frodo-new.jpg"
  },
  "categories": ["hobbits-of-the-shire", "ring-bearers"],
  "relations": {
    "OWNS": ["the-one-ring", "sting", "red-book-of-westmarch"]
  }
}
```

Ответ 200:

Полный объект страницы как `GET /pages/{slug}`

#### `DELETE /api/v1/pages/{slug}/`

Требует роль `admin`. Удаляет ноду и все её ребра из графа.

Ответ 204:
```
{} \\ Пустой
```

#### `POST /api/v1/pages/{slug}/like/`

Требует авторизации. Идемпотентен (!).

Ответ 200:
```
{ "likesCount": 43, "isLiked": true }
```

#### `DELETE /api/v1/pages/{slug}/like/`

Ответ 200:
```
{ "likesCount": 42, "isLiked": false }
```

#### `GET /api/v1/pages/{slug}/comments/`

Публичный. Пагинирован. Комментарии показываются на странице под текстом, но они отдельный запрос, а не часть `GET /pages/{slug}/`, потому что:
* их может быть очень много и нужна пагинация
* страница кэшируется агрессивно, комменты - нет
* фронт загружает их параллельно или после рендера страницы
```
?page=1&page_size=20
```

Ответ 200:
```
{
  "count":    7,
  "next":     null,
  "previous": null,
  "results": [
    {
      "id":   "3f2a1b4c-1234-5678-abcd-ef0123456789",
      "text": "One of my favourite characters!",
      "author": {
        "username":  "bilbo_baggins",
        "avatarUrl": null
      },
      "createdAt": "2024-03-15T10:00:00Z"
    }
  ]
}
```

#### `POST /api/v1/pages/{slug}/comments/`

Требует авторизации.

Запрос:
```
{ "text": "Amazing character arc." }
```

Ответ 201:
```
{
  "id":   "9d8c7b6a-...",
  "text": "Amazing character arc.",
  "author": {
    "username":  "bilbo_baggins",
    "avatarUrl": null
  },
  "createdAt": "2024-03-16T09:00:00Z"
}
```

Ответ 400 - пустой ответ:
```
{
  "error": {
    "code":    "VALIDATION_ERROR",
    "message": "Invalid input",
    "fields": {
      "text": ["This field may not be blank."]
    }
  }
}
```

#### `GET /api/v1/pages/{slug}/export/`

Требует роль `admin`. Скачивает JSON или CSV с данными одной страницы. Если JSON, то формат как у `GET /pages/{slug}`

Ответ 200:
```
Content-Disposition: attachment; filename="frodo-baggins.json"
Content-Type: application/json
```

#### `POST /api/v1/pages/{slug}/import/`

Требует роль `admin`. Обновляет данные страницы из JSON или CSV. Семантически эквивалентен PATCH, но принимает файл.

Запрос:
```
Content-Type: multipart/form-data
file: <frodo-baggins.json>
```

Ответ 200:

Полный объкет страницы после обновления.

Ответ 400:
```
{
  "error": {
    "code":    "INVALID_FORMAT",
    "message": "File must be a valid JSON page export.",
    "fields":  null
  }
}
```

### Каталоги - списки и создание

Чтение отдельной страницы через `/pages/{slug}`. Каталоги нужны, чтобы делать списки с фильтрацией и создавать новых сущностей. Создание типизированно, потому что у каждого типа своя схема валидации и обязательные поля.
```
GET  /api/v1/characters/
POST /api/v1/characters/
GET  /api/v1/races/
POST /api/v1/races/
GET  /api/v1/locations/
POST /api/v1/locations/
GET  /api/v1/events/
POST /api/v1/events/
GET  /api/v1/organizations/
POST /api/v1/organizations/
GET  /api/v1/timelines/
POST /api/v1/timelines/
GET  /api/v1/items/
POST /api/v1/items/
GET  /api/v1/languages/
POST /api/v1/languages/
GET  /api/v1/scripts/
POST /api/v1/scripts/
```

#### Формат элемента списка

В списке возвращается саммари-объект, не полная страница. Полные данные - только через запрос к странице. Это по идее снижает нагрузку и трафик.
```
{
  "slug":       "frodo-baggins",
  "type":       "character",
  "name":       "Frodo Baggins",
  "imageUrl":   "https://cdn.example.com/frodo.jpg",
  "notableFor": "Destroyed the One Ring",
  // + 2-3 поля, специфичных для типа (описаны ниже)
}
```

#### `GET /api/v1/characters/`
Ответ 200:
```
{
  "count": 150,
  "next":  "/api/v1/characters/?page=2",
  "previous": null,
  "results": [
    {
      "slug":       "frodo-baggins",
      "type":       "character",
      "name":       "Frodo Baggins",
      "imageUrl":   "...",
      "notableFor": "Destroyed the One Ring",
      "gender":     "male",
      "birthDate":  "TA 2968",
      "race":       { "slug": "hobbits", "name": "Hobbits" }
    }
  ]
}
```
Query parameters:
| Параметр | Тип | Описание |
|----------|-----|----------|
| `names` | string | подстрока в любом из `names` |
| `gender` | `male\|female\|unknown\|мб другие если есть` | точное совпадение |
| `birth_date` | string | подстрока в `birthDate` (напр. `TA`) |
| `death_date` | string | подстрока в `deathDate` |
| `is_alive` | bool | `deathDate is null` |
| `hair` | string | подстрока |
| `eyes` | string | подстрока |
| `height` | string | подстрока |
| `weapon` | string | подстрока |
| `clothing` | string | подстрока |
| `notable_for` | string | подстрока |
| `race` | string | slug расы |
| `organization` | string | slug организации |
| `location` | string | slug локации (lived_in ИЛИ born_in) |
| `event` | string | slug события |
| `item` | string | slug предмета (owns) |
| `sort` | `name\|birth_date\|death_date` | |
| `order` | `asc\|desc` | default `asc` |

Это просто прикидка, могут быть другие, Света готовься.

#### `POST /api/v1/characters/`

Требует роль `admin`.

Запрос:
```
{
  "slug":    "frodo-baggins",      // опционально - генерируется из names[0] если не передан
  "names":   ["Frodo Baggins"],    // обязательно
  "titles":  ["Ring-bearer"],
  "gender":  "male",               // обязательно: male|female|unknown
  "birthDate": "TA 2968",
  "deathDate": null,
  "hair":     "brown, curly",
  "eyes":     "blue",
  "height":   "3 feet 6 inches",
  "weapon":   "Sting",
  "clothing": "Hobbit clothes",
  "notableFor": "Destroyed the One Ring",
  "article": {
    "text":     "Frodo Baggins was...",
    "imageUrl": "https://cdn.example.com/frodo.jpg"
  },
  "categories": ["hobbits-of-the-shire"],
  "relations": {
    "BELONGS_TO_RACE": ["hobbits"],
    "BORN_IN":         ["the-shire"],
    "MEMBER_OF":       ["fellowship-of-the-ring"]
  }
}
```

Ответ 201:

Полный объект страницы

Ответ 409 - слаг занят:
```
{
  "error": {
    "code":    "CONFLICT",
    "message": "Page with slug 'frodo-baggins' already exists.",
    "fields":  { "slug": ["This slug is already taken."] }
  }
}
```

#### `GET /api/v1/races/`

Ответ 200:
```
// results item
{
  "slug":         "hobbits",
  "type":         "race",
  "name":         "Hobbits",
  "imageUrl":     "...",
  "distinctions": "Small stature, large hairy feet",
  "lifespan":     "100+ years",
  "avgHeight":    "3-4 feet"
}
```

Query parameters:

| Параметр | Описание |
|----------|----------|
| `names` | подстрока |
| `lifespan` | подстрока |
| `avg_height` | подстрока |
| `hair` | подстрока |
| `eyes` | подстрока |
| `skin` | подстрока |
| `weaponry` | подстрока |
| `clothing` | подстрока |
| `distinctions` | подстрока |
| `sort` | `name` |

Опять же может меняться

#### `GET /api/v1/locations/`

Ответ 200:
```
// results item
{
  "slug":         "the-shire",
  "type":         "location",
  "name":         "The Shire",
  "imageUrl":     "...",
  "locationType": "region",
  "notableFor":   "Home of the Hobbits",
  "creationDate": "TA 1601"
}
```

Query parameters:

| Параметр | Описание |
|----------|----------|
| `names` | подстрока |
| `type` | подстрока в `locationType` (river, mountain, city…) |
| `population` | подстрока |
| `creation_date` | подстрока |
| `destruction_date` | подстрока |
| `is_destroyed` | bool — `destructionDate is not null` |
| `notable_for` | подстрока |
| `character` | slug персонажа (lived_in ИЛИ born_in) |
| `event` | slug события (happened_in) |
| `organization` | slug организации |
| `sort` | `name\|creation_date\|destruction_date` |

#### `GET /api/v1/events/`

```
// results item
{
  "slug":      "war-of-the-ring",
  "type":      "event",
  "name":      "War of the Ring",
  "imageUrl":  null,
  "eventType": "war",
  "startDate": "TA 3018",
  "endDate":   "TA 3019"
}
```

Query parameters:

| Параметр | Описание |
|----------|----------|
| `names` | подстрока |
| `type` | подстрока в `eventType` |
| `start_date` | подстрока |
| `end_date` | подстрока |
| `casualties` | подстрока |
| `notable_for` | подстрока |
| `character` | slug участника |
| `location` | slug локации |
| `organization` | slug организации-участника |
| `sort` | `name\|start_date\|end_date` |

#### `GET /api/v1/organizations/`

```
// results item
{
  "slug":        "fellowship-of-the-ring",
  "type":        "organization",
  "name":        "Fellowship of the Ring",
  "imageUrl":    "...",
  "orgType":     "fellowship",
  "foundedDate": "TA 3018",
  "purpose":     "Destroy the One Ring"
}
```

Query parameters:

| Параметр | Описание |
|----------|----------|
| `names` | подстрока |
| `type` | подстрока в `orgType` |
| `founded_date` | подстрока |
| `dissolved_date` | подстрока |
| `is_active` | bool — `dissolvedDate is null` |
| `clothing` | подстрока |
| `weaponry` | подстрока |
| `purpose` | подстрока |
| `notable_for` | подстрока |
| `character` | slug члена |
| `location` | slug локации |
| `sort` | `name\|founded_date` |

#### `GET /api/v1/items/`

```
// results item
{
  "slug":      "the-one-ring",
  "type":      "item",
  "name":      "The One Ring",
  "imageUrl":  "...",
  "itemType":  "ring",
  "material":  "gold",
  "notableFor": "The One Ring to rule them all"
}
```

Query parameters:

| Параметр | Описание |
|----------|----------|
| `names` | подстрока |
| `type` | подстрока в `itemType` |
| `material` | подстрока |
| `notable_for` | подстрока |
| `owner` | slug персонажа-владельца |
| `location` | slug локации |
| `sort` | `name\|type` |

#### `GET /api/v1/timelines/`

```
// results item
{
  "slug":         "third-age",
  "type":         "timeline",
  "name":         "Third Age",
  "abbreviation": "TA",
  "startDate":    "SA 3441",
  "endDate":      "TA 3021"
}
```

Query parameters: `name`, `abbreviation`, `start_date`, `end_date`, `sort=name|start_date`

#### `GET /api/v1/languages/`

```
// results item
{
  "slug":   "quenya",
  "type":   "language",
  "name":   "Quenya",
  "family": "Elvish"
}
```

Query parameters: `names`, `family`, `sort=name`

#### `GET /api/v1/scripts/`

```
// results item
{
  "slug": "tengwar",
  "type": "script",
  "name": "Tengwar"
}
```

Query parameters: `names`, `sort=name`

### Пользователи
```
GET    /api/v1/users/                    [admin]
GET    /api/v1/users/{username}/
PATCH  /api/v1/users/{username}/         [admin]
DELETE /api/v1/users/{username}/         [admin]
```
Разграничение с `/auth/me/`: `me` — текущий пользователь управляет собой. `/users/` — публичные профили и административное управление.

#### `GET /api/v1/users/`

Требует роль `admin`. Возвращает расширенный объект с приватными полями (`email`, `role`).
```
?page=1&page_size=20
?username=bilbo     # подстрока, регистронезависимо
?role=viewer        # viewer | admin
?sort=username|created_at&order=asc|desc
```

Ответ 200:
```
{
  "count": 42,
  "next":  "/api/v1/users/?page=2",
  "previous": null,
  "results": [
    {
      "username":  "bilbo_baggins",
      "email":     "bilbo@shire.me",
      "role":      "viewer",
      "avatarUrl": null,
      "createdAt": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### `GET /api/v1/users/{username}/`

Публичный. Email и role не возвращаются — приватные данные. 

Ответ 200:
```
{
  "username":     "bilbo_baggins",
  "avatarUrl":    "https://cdn.example.com/avatars/bilbo.jpg",
  "createdAt":    "2024-01-01T00:00:00Z",
  "commentsCount": 12,
  "likedPages": [
    { "slug": "frodo-baggins", "name": "Frodo Baggins", "type": "character" },
    { "slug": "the-shire",     "name": "The Shire",     "type": "location"  }
  ]
}
```

Ответ 404:
```
{
  "error": {
    "code":    "NOT_FOUND",
    "message": "User 'bilbo_bagginss' does not exist.",
    "fields":  null
  }
}
```

#### `PATCH /api/v1/users/{username}/`

Требует роль `admin`. Только для управления ролью. Редактирование чужого профиля (`username`, `email`, `avatar`) через этот эндпоинт должно быть недоступно - пользователь делает это сам через `PATCH /auth/me/`.

Запрос:
```
{ "role": "admin" }
```

Ответ 200:
```
{
  "username":  "bilbo_baggins",
  "email":     "bilbo@shire.me",
  "role":      "admin",
  "avatarUrl": null,
  "createdAt": "2024-01-01T00:00:00Z"
}
```

Ответ 400 - невалидная роль:
```
{
  "error": {
    "code":    "VALIDATION_ERROR",
    "message": "Invalid input",
    "fields": {
      "role": ["Must be one of: viewer, admin."]
    }
  }
}
```

#### `DELETE /api/v1/users/{username}/`

Требует роль `admin`. Нельзя удалить самого себя.

Ответ 204: пустой

Ответ 403 - попытка удалить себя:
```
{
  "error": {
    "code":    "FORBIDDEN",
    "message": "You cannot delete your own account.",
    "fields":  null
  }
}
```

### Глобальный поиск
```
GET /api/v1/search/
```

Используется для поисковой строки в навбаре (автодополнение при вводе) и для поля выбора сущностей на странице аналитики.

Query parameters:

| Параметр | Тип | Описание |
|----------|-----|----------|
| `q` | string | строка поиска, min 2 символа, обязательно |
| `types` | string | типы через запятую; default - все типы |
| `limit` | int | max результатов; default 5, max 20 |

Поиск по подстроке в `names` всех узлов через fulltext-индекс Neo4j - один запрос по всему графу.

Ответ 200:
```
// GET /api/v1/search/?q=frod&limit=5
[
  { "slug": "frodo-baggins", "type": "character", "name": "Frodo Baggins", "imageUrl": "..." },
  { "slug": "frodina",       "type": "character", "name": "Frodina",       "imageUrl": null  }
]

```

Ответ 400 - слишком короткий запрос:
```
{
  "error": {
    "code":    "VALIDATION_ERROR",
    "message": "Query must be at least 2 characters.",
    "fields":  { "q": ["Ensure this value has at least 2 characters."] }
  }
}
```

### Аналитика

По идее у страницы аналитики два режима (хз как мы будем это отображать, мб разные страницы): один узел (связи) и два узла (путь между узлами). Оба режима управляются URL-парметрами, которые фронт читает при монтировании. URL синхронизируется с состоянием страницы через `useSearchParams` - ссылку можно шарить или открыть с предзаполненными полями с карточки сущности.
```
/analytics                               # оба поля пусты
/analytics?from=frodo-baggins            # предзаполнен from - режим одного узла
/analytics?from=frodo-baggins&to=aragorn # оба - режим пути
```

#### `GET /api/v1/analytics/global/`

Публичный. Агрегированная статистика по всей вселенной.

Ответ 200:
```
{
  "counts": {
    "total":         540,
    "characters":    150,
    "races":          20,
    "locations":      80,
    "events":         60,
    "organizations":  50,
    "timelines":       5,
    "items":          70,
    "languages":      25,
    "scripts":        10,
    "articles":       480
  },
  "charactersByRace": [
    { "slug": "elves",   "name": "Elves",   "count": 47 },
    { "slug": "hobbits", "name": "Hobbits", "count": 32 }
  ],
  "charactersBySide": [
    { "side": "good",    "count": 89 },
    { "side": "evil",    "count": 45 },
    { "side": "neutral", "count": 16 }
  ],
  "topConnected": {
    "characters": [
      { "slug": "gandalf", "name": "Gandalf", "connectionsCount": 47 },
      { "slug": "aragorn", "name": "Aragorn", "connectionsCount": 38 }
    ],
    "locations": [
      { "slug": "rivendell", "name": "Rivendell", "connectionsCount": 29 }
    ],
    "events": [
      { "slug": "war-of-the-ring", "name": "War of the Ring", "connectionsCount": 55 }
    ],
    "organizations": [
      { "slug": "fellowship-of-the-ring", "name": "Fellowship of the Ring", "connectionsCount": 31 }
    ],
    "items": [
      { "slug": "the-one-ring", "name": "The One Ring", "connectionsCount": 18 }
    ]
  }
}
```

#### `GET /api/v1/analytics/neighbors/`

Публичный. Возвращает граф соседей узла (nodes + edges). В v0.5 рендерим как список, в v0.8 уже рисуем граф.

Query parameters:

| Параметр | Тип | Описание |
|----------|-----|----------|
| `entity` | string | slug узла, обязательно |
| `node_types` | string | типы через запятую; default - все |
| `rel_types` | string | типы рёбер через запятую; default - все |
| `depth` | int | глубина обхода: `1` или `2`; default `1` |

Ответ 200:
```
// GET /api/v1/analytics/neighbors/?entity=frodo-baggins&node_types=character,location
{
  "root": {
    "slug": "frodo-baggins",
    "type": "character",
    "name": "Frodo Baggins",
    "imageUrl": "..."
  },
  "nodes": [
    { "slug": "the-shire",    "type": "location",  "name": "The Shire",    "imageUrl": "..." },
    { "slug": "bag-end",      "type": "location",  "name": "Bag End",      "imageUrl": null  },
    { "slug": "samwise-gamgee","type": "character", "name": "Samwise Gamgee","imageUrl": "..." }
  ],
  "edges": [
    { "from": "frodo-baggins", "to": "the-shire",     "type": "BORN_IN"  },
    { "from": "frodo-baggins", "to": "bag-end",       "type": "LIVED_IN" },
    { "from": "frodo-baggins", "to": "samwise-gamgee","type": "KNOWS"    }
  ],
  "stats": {
    "totalNeighbors": 3,
    "byType": {
      "character": 1,
      "location":  2
    },
    "byRelation": {
      "BORN_IN":  1,
      "LIVED_IN": 1,
      "KNOWS":    1
    }
  }
}
```

Ответ 400: entity не передан

Ответ 404: entity не найден

### `GET /api/v1/analytics/shortest-path/`

Публичный. `through` обязателен: без него граф слишком большой для обхода и запрос семантически некорректен.

Query parameters:

| Параметр | Тип | Описание |
|----------|-----|----------|
| `from` | string | slug начального узла, обязательно |
| `to` | string | slug конечного узла, обязательно |
| `through-nodes` | string | типы промежуточных узлов через запятую, обязательно |
| `through-rels` | string | типы связей между промежуточными узлами через запятую, обязательно |

Тут параметры точно поменяются, нужно придумать что-то покрасивее, мне пока лень :).

Ответ 200:
```
// GET /api/v1/analytics/shortest-path/?from=frodo-baggins&to=aragorn&through=character,organization
{
  "found":  true,
  "length": 3,
  "from": { "slug": "frodo-baggins", "type": "character", "name": "Frodo Baggins", "imageUrl": "..." },
  "to":   { "slug": "aragorn",       "type": "character", "name": "Aragorn",       "imageUrl": "..." },
  "path": [
    {
      "node":        { "slug": "frodo-baggins",          "type": "character",    "name": "Frodo Baggins",          "imageUrl": "..." },
      "edgeToNext":  { "type": "MEMBER_OF", "label": "member of" }
    },
    {
      "node":        { "slug": "fellowship-of-the-ring", "type": "organization", "name": "Fellowship of the Ring", "imageUrl": "..." },
      "edgeToNext":  { "type": "MEMBER_OF", "label": "member of" }
    },
    {
      "node":        { "slug": "aragorn", "type": "character", "name": "Aragorn", "imageUrl": "..." },
      "edgeToNext":  null
    }
  ]
}
```

Ответ 200: путь не найден

Не 404 - запрос корректен, это просто пути нет (ну или есть, но нулевой длины)
```
{
  "found":  false,
  "length": null,
  "from": { "slug": "frodo-baggins", "type": "character", "name": "Frodo Baggins", "imageUrl": "..." },
  "to":   { "slug": "sauron",        "type": "character", "name": "Sauron",        "imageUrl": "..." },
  "path": []
}
```

Ответ 400 - from == to:
```
{
  "error": {
    "code":    "VALIDATION_ERROR",
    "message": "Start and end nodes must be different.",
    "fields":  { "to": ["Must be different from 'from'."] }
  }
}
```

Ответ 400 - какой-то из through_* не передан:
```
{
  "error": {
    "code":    "VALIDATION_ERROR",
    "message": "At least one node type must be specified in 'through'.",
    "fields":  { "through": ["This field is required."] }
  }
}
```

#### `GET /api/v1/analytics/custom/`

Публичный. Кастомизируемая статистика - данные для построения графика по выбранным атрибутам.

Query parameters:

| Параметр | Тип | Описание |
|----------|-----|----------|
| `entity_type` | string | тип сущности, обязательно |
| `x_attr` | string | атрибут для группировки (ось X) |
| `y_attr` | string | атрибут для агрегации (ось Y) |
| `agg` | `count` | функция агрегации; default `count` |
| фильтры каталога | | те же параметры, что в `GET /characters/` и т.д. |

Ответ 200:
```
// GET /api/v1/analytics/custom/?entity_type=character&x_attr=race&y_attr=gender&agg=count&is_alive=true
{
  "entityType": "character",
  "xAttr":      "race",
  "yAttr":      "gender",
  "agg":        "count",
  "data": [
    { "x": "Hobbits", "y": "male",   "value": 8  },
    { "x": "Hobbits", "y": "female", "value": 4  },
    { "x": "Elves",   "y": "male",   "value": 21 },
    { "x": "Elves",   "y": "female", "value": 18 }
  ]
}
```

Ответ 400 - entity-type не передан.

### Массовый импорт/экспорт

Требует роль `admin`.

#### `GET /api/v1/bulk/export/`

Скачивает JSON с полными данными всего приложения.

Ответ 200:
```
Content-Disposition: attachment; filename="lotr-wiki-export-2024-03-16.json"
Content-Type: application/json
```

#### `POST /api/v1/bulk/import/`

Загружает файл в формате экспорта. Существующие сущности (по слагу) обновляются, новые — создаются.

Запрос:
```
Content-Type: multipart/form-data
file: <lotr-wiki-export.json>
```

Ответ 200:
```
{
  "imported": {
    "characters":    12,
    "races":          4,
    "locations":      8,
    "events":         5,
    "organizations":  3,
    "timelines":      5,
    "items":          7,
    "languages":      6,
    "scripts":        3
  },
  "skipped":  2,
  "errors":   [
    { "slug": "broken-entity", "reason": "Required field 'names' is missing." }
  ]
}
```

Ответ 400 - невалидный формат файла:
```
{
  "error": {
    "code":    "INVALID_FORMAT",
    "message": "File must be a valid JSON export (version 1).",
    "fields":  null
  }
}
```

### Метаданные

Хардкод на бэкенде, без обращения к БД. Нужны фронту для дропдаунов при создании/редактировании сущностей и при фильтрации соседей - чтобы фронт не хардкодил типы у себя.

#### `GET /api/v1/meta/node-types/`

```
[
  { "type": "character",    "label": "Character",    "pluralLabel": "Characters"    },
  { "type": "race",         "label": "Race",         "pluralLabel": "Races"         },
  { "type": "location",     "label": "Location",     "pluralLabel": "Locations"     },
  { "type": "event",        "label": "Event",        "pluralLabel": "Events"        },
  { "type": "organization", "label": "Organization", "pluralLabel": "Organizations" },
  { "type": "timeline",     "label": "Timeline",     "pluralLabel": "Timelines"     },
  { "type": "item",         "label": "Item",         "pluralLabel": "Items"         },
  { "type": "language",     "label": "Language",     "pluralLabel": "Languages"     },
  { "type": "script",       "label": "Script",       "pluralLabel": "Scripts"       }
]
```

#### `GET /api/v1/meta/relation-types/`

```
[
  { "type": "BELONGS_TO_RACE", "label": "Belongs to race",   "from": ["character"],                "to": ["race"]         },
  { "type": "MEMBER_OF",       "label": "Member of",         "from": ["character"],                "to": ["organization"] },
  { "type": "PARTICIPATED_IN", "label": "Participated in",   "from": ["character"],                "to": ["event"]        },
  { "type": "BORN_IN",         "label": "Born in",           "from": ["character"],                "to": ["location"]     },
  { "type": "LIVED_IN",        "label": "Lived in",          "from": ["character"],                "to": ["location"]     },
  { "type": "KNOWS",           "label": "Knows",             "from": ["character"],                "to": ["character"]    },
  { "type": "PARENT_OF",       "label": "Parent of",         "from": ["character"],                "to": ["character"]    },
  { "type": "CHILD_OF",        "label": "Child of",          "from": ["character"],                "to": ["character"]    },
  { "type": "OWNS",            "label": "Owns",              "from": ["character"],                "to": ["item"]         },
  { "type": "RULED_BY",        "label": "Ruled by",          "from": ["location"],                 "to": ["character"]    },
  { "type": "LOCATED_IN",      "label": "Located in",        "from": ["location"],                 "to": ["location"]     },
  { "type": "HAPPENED_IN",     "label": "Happened in",       "from": ["event"],                    "to": ["location"]     },
  { "type": "SPEAKS",          "label": "Speaks",            "from": ["character", "race"],        "to": ["language"]     },
  { "type": "DURING",          "label": "During",            "from": ["event"],                    "to": ["timeline"]     },
  { "type": "PART_OF",         "label": "Part of",           "from": ["event"],                    "to": ["event"]        },
  { "type": "IN_CATEGORY",     "label": "In category",       "from": ["character", "location", "event", "organization", "item", "race", "timeline", "language", "script"], "to": ["category"] }
]
```

### Про статус коды

Возможно где-то забыл или неправильно поставил, но логика такая:

| Код | Когда кидается |
|-----|-------|
| `200 OK` | Успешный `GET`, `PATCH` |
| `201 Created` | Успешный `POST` создания |
| `204 No Content` | Успешный `DELETE` |
| `400 Bad Request` | Ошибка валидации входных данных |
| `401 Unauthorized` | Нет токена или токен невалиден |
| `403 Forbidden` | Токен валиден, но прав недостаточно (не `admin`) |
| `404 Not Found` | Ресурс не найден |
| `409 Conflict` | Конфликт — например, слаг уже занят |
| `422 Unprocessable Entity` | Семантически некорректный запрос (напр., `from == to` в shortest-path) |