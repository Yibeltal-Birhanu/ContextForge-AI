"""
Technology normalization for ContextForge.

Converts compound technology strings like:
  "Next.js 14+ (App Router) with React 18 and TypeScript"
  "aws fargate behind application load balancer"
  "PostgreSQL 15+ on Amazon RDS with PostGIS"

Into canonical tokens:
  {"next.js", "react", "typescript"}
  {"aws fargate", "aws alb"}
  {"postgresql", "amazon rds", "postgis"}
"""

import re

# Known technology aliases — maps variants to canonical names
TECH_ALIASES: dict[str, str] = {
    # Frontend
    "react.js": "react",
    "reactjs": "react",
    "react 18": "react",
    "react 19": "react",
    "next.js": "next.js",
    "nextjs": "next.js",
    "next.js 14": "next.js",
    "next.js 15": "next.js",
    "next 14": "next.js",
    "next 15": "next.js",
    "vue.js": "vue",
    "vuejs": "vue",
    "angular.js": "angular",
    "angularjs": "angular",
    "svelte.js": "svelte",
    "sveltejs": "svelte",
    "nuxt.js": "nuxt",
    "nuxtjs": "nuxt",
    "remix.run": "remix",
    "flutter": "flutter",
    "react native": "react native",

    # Backend
    "node.js": "node.js",
    "nodejs": "node.js",
    "express.js": "express",
    "expressjs": "express",
    "fastapi": "fastapi",
    "fast api": "fastapi",
    "django": "django",
    "flask": "flask",
    "spring boot": "spring boot",
    "springboot": "spring boot",
    "laravel": "laravel",
    "ruby on rails": "rails",
    "rails": "rails",
    "gin": "gin",
    "fiber": "fiber",
    "actix": "actix",
    "actix web": "actix",
    "dotnet": ".net",
    "asp.net": "asp.net",
    "aspx": "asp.net",

    # Languages
    "typescript": "typescript",
    "ts": "typescript",
    "javascript": "javascript",
    "js": "javascript",
    "python": "python",
    "py": "python",
    "golang": "go",
    "golong": "go",
    "rustlang": "rust",
    "c sharp": "c#",
    "csharp": "c#",
    "kotlin": "kotlin",
    "swift": "swift",
    "java": "java",
    "php": "php",
    "ruby": "ruby",

    # Databases
    "postgres": "postgresql",
    "postgres db": "postgresql",
    "postgresql": "postgresql",
    "psql": "postgresql",
    "sql server": "sql server",
    "mssql": "sql server",
    "microsoft sql server": "sql server",
    "ms sql": "sql server",
    "mysql": "mysql",
    "mariadb": "mariadb",
    "mongodb": "mongodb",
    "mongo": "mongodb",
    "redis": "redis",
    "sqlite": "sqlite",
    "sqlite3": "sqlite",
    "dynamodb": "dynamodb",
    "dynamo": "dynamodb",
    "cassandra": "cassandra",
    "couchdb": "couchdb",
    "couchbase": "couchbase",
    "firebase firestore": "firestore",
    "firestore": "firestore",
    "supabase": "supabase",
    "planetscale": "planetscale",
    "neon": "neon",

    # Cloud / Infrastructure
    "aws": "aws",
    "amazon web services": "aws",
    "amazon aws": "aws",
    "aws fargate": "aws fargate",
    "fargate": "aws fargate",
    "aws ecs": "aws ecs",
    "ecs": "aws ecs",
    "aws ecr": "aws ecr",
    "ecr": "aws ecr",
    "aws lambda": "aws lambda",
    "lambda": "aws lambda",
    "aws s3": "aws s3",
    "s3": "aws s3",
    "s3-compatible storage": "s3-compatible storage",
    "s3-compatible object storage": "s3-compatible storage",
    "aws rds": "aws rds",
    "rds": "aws rds",
    "amazon rds": "aws rds",
    "aws alb": "aws alb",
    "application load balancer": "aws alb",
    "alb": "aws alb",
    "aws cloudfront": "aws cloudfront",
    "cloudfront": "aws cloudfront",
    "aws api gateway": "aws api gateway",
    "api gateway": "aws api gateway",
    "aws sqs": "aws sqs",
    "sqs": "aws sqs",
    "aws sns": "aws sns",
    "sns": "aws sns",
    "aws iam": "aws iam",
    "iam": "aws iam",

    "google cloud": "gcp",
    "gcp": "gcp",
    "google cloud platform": "gcp",
    "gke": "gke",
    "google kubernetes engine": "gke",
    "cloud run": "google cloud run",
    "google cloud run": "google cloud run",
    "cloud functions": "google cloud functions",

    "azure": "azure",
    "microsoft azure": "azure",
    "azure containers": "azure aci",
    "azure container instances": "azure aci",

    "docker": "docker",
    "dockerfile": "docker",
    "docker compose": "docker compose",
    "docker containers": "containers",
    "containerized": "containers",
    "containerization": "containers",
    "containers": "containers",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "helm": "helm",

    "vercel": "vercel",
    "netlify": "netlify",
    "heroku": "heroku",
    "render": "render",
    "railway": "railway",
    "fly.io": "fly.io",
    "fly": "fly.io",
    "digitalocean": "digitalocean",
    "hetzner": "hetzner",
    "infisical": "infisical",
    "do spaces": "digitalocean",

    # Auth — concrete technologies only
    "jwt": "jwt",
    "json web token": "jwt",
    "jsonwebtoken": "jwt",
    "oauth": "oauth",
    "oauth2": "oauth2",
    "oauth 2.0": "oauth2",
    "google oauth": "google oauth",
    "linkedin oauth": "linkedin oauth",
    "openid connect": "openid connect",
    "oidc": "openid connect",
    "auth0": "auth0",
    "firebase auth": "firebase auth",
    "clerk": "clerk",
    "supabase auth": "supabase auth",
    "asp.net identity": "asp.net identity",
    "django auth": "django auth",
    "docker secrets": "docker secrets",

    # Payments
    "stripe": "stripe",
    "paypal": "paypal",
    "chapa": "chapa",
    "telebirr": "telebirr",
    "budpay": "budpay",
    "paystack": "paystack",
    "razorpay": "razorpay",

    # Messaging / Notifications
    "twilio": "twilio",
    "africas talking": "africas talking",
    "africa's talking": "africas talking",
    "africastalking": "africas talking",
    "sendgrid": "sendgrid",
    "mailgun": "mailgun",
    "firebase messaging": "firebase messaging",
    "fcm": "fcm",
    "firebase cloud messaging": "fcm",
    "pusher": "pusher",
    "socket.io": "socket.io",
    "socketio": "socket.io",
    "websockets": "websockets",
    "websocket": "websockets",

    # AI / ML — concrete technologies only, NOT concepts
    "openai": "openai",
    "openai api": "openai",
    "gpt-4": "openai gpt-4",
    "gpt-3.5": "openai gpt-3.5",
    "chatgpt": "openai",
    "claude": "anthropic",
    "anthropic": "anthropic",
    "tensorflow": "tensorflow",
    "pytorch": "pytorch",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "hugging face": "huggingface",
    "huggingface": "huggingface",
    "langchain": "langchain",
    "amazon bedrock": "amazon bedrock",
    "aws bedrock": "amazon bedrock",
    "google vertex ai": "google vertex ai",
    "azure openai": "azure openai",
    "pandas": "pandas",
    "numpy": "numpy",
    "matplotlib": "matplotlib",

    # ORM / Database tools
    "prisma": "prisma",
    "typeorm": "typeorm",
    "sequelize": "sequelize",
    "mongoose": "mongoose",
    "sqlalchemy": "sqlalchemy",
    "alembic": "alembic",
    "drizzle": "drizzle",
    "knex": "knex",
    "entity framework": "entity framework",
    "entity framework core": "entity framework",
    "ef core": "entity framework",
    "hibernate": "hibernate",
    "django orm": "django orm",

    # Version Control
    "git": "git",
    "github": "github",
    "gitlab": "gitlab",

    # CI/CD
    "github actions": "github actions",
    "gitlab ci": "gitlab ci",
    "gitlab ci/cd": "gitlab ci",
    "aws codepipeline": "aws codepipeline",
    "codepipeline": "aws codepipeline",
    "circleci": "circleci",
    "circle ci": "circleci",
    "jenkins": "jenkins",

    # Testing
    "jest": "jest",
    "mocha": "mocha",
    "pytest": "pytest",
    "unittest": "unittest",
    "vitest": "vitest",
    "cypress": "cypress",
    "playwright": "playwright",
    "selenium": "selenium",

    # CSS / UI
    "tailwind": "tailwindcss",
    "tailwind css": "tailwindcss",
    "tailwindcss": "tailwindcss",
    "bootstrap": "bootstrap",
    "material ui": "material ui",
    "mui": "material ui",
    "chakra ui": "chakra ui",
    "shadcn": "shadcn",
    "shadcn ui": "shadcn",

    # API protocols — concrete technologies
    "graphql": "graphql",
    "grpc": "grpc",
    "trpc": "trpc",
    "swagger": "swagger",
    "openapi": "openapi",

    # Search
    "elasticsearch": "elasticsearch",
    "opensearch": "opensearch",
    "meilisearch": "meilisearch",
    "algolia": "algolia",

    # Monitoring / Observability — concrete tools
    "sentry": "sentry",
    "datadog": "datadog",
    "prometheus": "prometheus",
    "grafana": "grafana",
    "new relic": "new relic",
    "logRocket": "logrocket",
    "logrocket": "logrocket",

    # Web servers / Reverse proxy
    "nginx": "nginx",
    "apache": "apache",
    "traefik": "traefik",
    "caddy": "caddy",

    # Web/Vite
    "vite": "vite",
    "webpack": "webpack",
    "esbuild": "esbuild",
    "rollup": "rollup",

    # Browsers / Testing tools
    "puppeteer": "puppeteer",
    "chrome": "chrome",

    # .NET ecosystem
    ".net": ".net",
    ".net core": ".net",
    ".net 6": ".net",
    ".net 7": ".net",
    ".net 8": ".net",
    "asp.net": "asp.net",
    "asp.net core": "asp.net core",
    "blazor": "blazor",
    "maui": "maui",
    ".net maui": ".net maui",
    "xamarin": "xamarin",
    "uwp": "uwp",
    "winui": "winui",

    # Java ecosystem
    "spring": "spring",
    "spring mvc": "spring",
    "spring cloud": "spring cloud",
    "quarkus": "quarkus",
    "micronaut": "micronaut",
    "jpa": "jpa",
    "hibernate": "hibernate",
    "mybatis": "mybatis",

    # Data / Analytics
    "pandas": "pandas",
    "numpy": "numpy",
    "scipy": "scipy",
    "matplotlib": "matplotlib",
    "plotly": "plotly",
    "jupyter": "jupyter",
    "apache spark": "apache spark",
    "spark": "apache spark",
    "apache kafka": "apache kafka",
    "kafka": "apache kafka",
    "apache flink": "apache flink",
    "airflow": "airflow",
    "apache airflow": "airflow",
    "dbt": "dbt",
    "snowflake": "snowflake",
    "bigquery": "bigquery",
    "google bigquery": "bigquery",
    "redshift": "redshift",
    "aws redshift": "redshift",
    "databricks": "databricks",
    "trino": "trino",
    "presto": "presto",

    # Mobile
    "react native": "react native",
    "flutter": "flutter",
    "dart": "dart",
    "kotlin multiplatform": "kotlin multiplatform",
    "swiftui": "swiftui",
    "uikit": "uikit",
    "jetpack compose": "jetpack compose",
    "compose multiplatform": "compose multiplatform",
    "nativescript": "nativescript",
    "ionic": "ionic",
    "capacitor": "capacitor",
    "cordova": "cordova",
    "expo": "expo",
}
# ============================================================
# NON-TECHNOLOGY WORDS
# ============================================================
# These are domain concepts, capabilities, or architectural patterns.
# They must NEVER be classified as technologies.
NON_TECH_WORDS: set[str] = {
    # Architectural concepts
    "backend", "frontend", "fullstack", "full-stack", "full stack",
    "web", "mobile", "desktop", "server", "client",
    "api", "rest", "rest api", "restful",
    "microservice", "microservices", "monolith", "monolithic",
    "serverless", "edge",

    # Domain concepts
    "database", "authentication", "authorization", "authorization",
    "payment", "payments", "notification", "notifications",
    "messaging", "messaging", "sms", "email", "push notification",
    "search", "filtering", "pagination", "sorting",
    "dashboard", "admin", "admin panel", "user management",
    "appointment", "appointments", "booking", "reservation",
    "reminder", "reminders", "alert", "alerts",
    "profile", "profiles", "user profile",
    "login", "signup", "sign up", "sign in", "logout",
    "registration", "onboarding",
    "upload", "download", "file upload",
    "report", "reports", "analytics", "statistics",
    "chat", "messaging", "forum", "comment",
    "rating", "review", "reviews", "feedback",
    "cart", "shopping cart", "checkout",
    "inventory", "stock", "warehouse",
    "invoice", "billing", "subscription",
    " otp ", "otp", "one-time password",
    "health", "healthcare", "medical", "clinical",
    "patient", "patients", "doctor", "doctors",
    "clinic", "clinics", "hospital", "hospitals",
    "appointment scheduling", "telemedicine",

    # Technology concepts (not concrete technologies)
    "ai", "artificial intelligence", "machine learning", "ml",
    "deep learning", "neural network", "nlp",
    "natural language processing", "computer vision",
    "llm", "large language model", "generative ai",
    "data science", "data engineering",
    "devops", "infrastructure", "deployment",
    "hosting", "cloud", "on-premise", "on premise",
    "orchestration",
    "monitoring", "logging", "metrics", "observability",
    "security", "encryption", "firewall",
    "caching", "queue", "message queue",
    "real-time", "realtime", "real time",
    "long polling",
    "background job", "background worker", "cron job",
    "ci", "cd", "ci/cd", "continuous integration", "continuous deployment",
    "testing", "unit testing", "integration testing",
    "e2e", "end to end", "end-to-end",
    "documentation", "api documentation",
    "localization", "i18n", "l10n",
    "accessibility", "a11y",
    "performance", "optimization",
    "scalability", "high availability",
    "disaster recovery", "backup",
    "staging", "production", "development", "testing environment",
    "platform", "service", "worker", "job",
    "integration", "third-party", "third party",
    "workflow", "pipeline", "process",
    "state management", "data flow",
    "ui", "ux", "user interface", "user experience",
    "design system", "component library",
    "content management", "cms",
    "seo", "search engine optimization",
    "ab testing", "a/b testing",
    "feature flag", "feature flags",
    "rate limiting", "throttling",
    "load balancing", "reverse proxy",
    "cdn", "content delivery network",
    "dns", "domain name",
    "ssl", "tls", "https", "certificate",
    "oauth", "openid", "saml", "sso",
    "rbac", "role-based", "acl", "permissions",
    "audit", "audit log", "compliance",
    "restore", "migration",
    "schema", "model", "entity", "table",
    "query", "mutation", "subscription",
    "middleware", "interceptor", "filter",
    "hook", "callback", "event", "listener",
    "cache", "session", "cookie",
    "token", "refresh token", "access token",
    "cors", "csrf", "xss", "injection",
    "kubernetes", "k8s", "helm",
    "terraform", "cloudformation", "pulumi",
    "ansible", "chef", "puppet", "salt",
    "sonarqube", "sonar", "linting",
    "editor", "ide", "vscode", "intellij",
    "gitlab ci", "bitbucket",
    "agile", "scrum", "kanban", "sprint",
    "mvc", "mvvm", "mvp", "clean architecture",
    "ddd", "domain driven", "event sourcing",
    "cqrs", "saga", "choreography",
    "pub/sub", "publish subscribe",
    "protobuf", "thrift",
    "amqp", "mqtt", "stomp",
    "etl", "elt", "data pipeline",
    "olap", "oltp", "data warehouse",
    "data lake", "data mesh",
    "feature store", "model registry",
    "mlops", "model deployment", "inference",
    "training", "fine-tuning", "fine tuning",
    "embedding", "vector database", "rag",
    "prompt engineering", "chain of thought",
    "agent", "multi-agent", "tool use",
    "function calling", "tool calling",
    "grounding", "retrieval", "augmented generation",
}


def normalize_tech_name(raw: str) -> str:
    """Normalize a single technology name to its canonical form."""
    name = raw.strip().lower()

    # Remove version numbers: "react 18" -> "react", "Next.js 14+" -> "next.js"
    name = re.sub(r'\s*\d+(\.\d+)*\+?(\.\.\.)?\s*$', '', name)
    name = re.sub(r'\s*v?\d+(\.\d+)*\+?\s*$', '', name)
    name = re.sub(r'\s*\d+\+?\s*$', '', name)

    # Remove parenthetical qualifiers: "(App Router)" "(TypeScript)"
    name = re.sub(r'\s*\(.*?\)\s*', ' ', name).strip()

    # Remove non-tech tokens entirely
    non_tech_tokens = {
        'behind', 'behind an', 'behind a', 'behind the',
        'internal', 'adapter', 'internal adapter',
        'managed', 'hosting', 'cloud',
        'ai diagnosis', 'ai powered', 'ai-based',
        'machine learning model', 'deep learning model',
    }
    if name in non_tech_tokens:
        return ''

    # Check against NON_TECH_WORDS — generic domain concepts
    # that must never be treated as technologies
    if name in NON_TECH_WORDS:
        return ''

    # EARLY ALIAS CHECK: Check aliases BEFORE suffix stripping.
    # This prevents "Firebase Cloud Messaging" from being stripped to
    # "firebase cloud" when the alias maps it to "fcm".
    if name in TECH_ALIASES:
        return TECH_ALIASES[name]

    # Remove common suffixes that don't add tech identity
    suffixes_to_strip = [
        ' authentication', ' authorization', ' hosting', ' deployment',
        ' database', ' server', ' client', ' service', ' integration',
        ' management', ' monitoring', ' logging', ' caching',
        ' payment processing', ' payments', ' messaging', ' notifications',
        ' container hosting', ' managed container hosting',
        ' managed hosting', ' cloud hosting',
        ' behind an application load balancer',
        ' behind application load balancer',
        ' behind alb',
        ' behind an internal adapter',
        ' behind internal adapter',
        ' behind an adapter',
        ' behind adapter',
        ' internal adapter',
        ' adapter',
        ' behind an', ' behind a', ' behind the', ' behind',
        ' for ai diagnosis', ' for diagnosis',
        ' for machine learning', ' for ml',
        ' for ai', ' for machine',
    ]
    for suffix in suffixes_to_strip:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()

    # Clean up remaining artifacts
    name = name.strip()
    if not name:
        return ''

    # Remove leading/trailing non-tech words
    name = re.sub(r'^(?:behind|internal|external|managed|self-hosted|cloud|on-premise)\s+', '', name)

    # Check exact alias match
    if name in TECH_ALIASES:
        return TECH_ALIASES[name]

    # Check without common suffixes
    cleaned = name.rstrip(".")
    if cleaned in TECH_ALIASES:
        return TECH_ALIASES[cleaned]

    # Final cleanup: remove very short tokens that are clearly not tech
    if len(name) <= 2 and name not in ('go', 'r', 'c#'):
        return ''

    return name


def normalize_tech_list(raw_list: list[str]) -> set[str]:
    """
    Normalize a list of technology strings into a set of canonical names.

    Input:
      ["Next.js 14+ (App Router) with React 18 and TypeScript",
       "PostgreSQL 15+ on Amazon RDS"]

    Output:
      {"next.js", "react", "typescript", "postgresql", "amazon rds"}
    """
    result = set()
    for raw in raw_list:
        tokens = _split_compound(raw)
        for token in tokens:
            canonical = normalize_tech_name(token)
            if canonical and len(canonical) > 1:
                result.add(canonical)
    return result


def dedupe_technology_strings(raw_list: list[str]) -> list[str]:
    """Keep descriptive technology entries and drop later duplicate aliases."""
    def tokens_for(raw: str) -> set[str]:
        tokens = normalize_tech_list([raw])
        lowered = raw.lower()
        for alias, canonical in TECH_ALIASES.items():
            if re.search(r"(?<![\w-])" + re.escape(alias) + r"(?![\w-])", lowered):
                tokens.add(canonical)
        return tokens

    result = []
    seen = set()
    for raw in raw_list:
        tokens = tokens_for(raw)
        if tokens and tokens <= seen:
            continue
        result.append(raw)
        seen.update(tokens)
    return result


def _split_compound(text: str) -> list[str]:
    """
    Split a compound technology string into individual tokens.

    "Next.js 14+ (App Router) with React 18 and TypeScript"
    -> ["Next.js 14+ (App Router)", "React 18", "TypeScript"]
    """
    text = text.strip()
    if not text:
        return []

    # First split on "," to handle comma-separated lists
    segments = text.split(",")

    result = []
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue

        # Extract parenthetical alternatives: "chapa (or telebirr)" -> ["chapa", "telebirr"]
        # But skip location/context info like "(ethiopia)"
        paren_matches = re.findall(r'\((?:or|and)?\s*(.+?)\)', segment)
        for pm in paren_matches:
            pm_clean = pm.strip().lower()
            # Skip if it looks like a location or non-tech context
            if pm_clean in ('ethiopia', 'nigeria', 'kenya', 'ghana', 'tanzania', 'uganda',
                           'production', 'development', 'staging', 'backend', 'frontend',
                           'internal', 'external', 'managed', 'self-hosted'):
                continue
            result.append(pm.strip())

        # Remove parenthetical content for further processing
        segment = re.sub(r'\(.*?\)', '', segment).strip()

        # Split on " - " which is commonly used as "Technology - Description"
        # e.g. "React - Frontend UI framework" -> "React"
        if " - " in segment:
            # Take only the part before the first " - "
            segment = segment.split(" - ")[0].strip()

        # Split on conjunctions: and, with, or, behind, on, for, via
        parts = re.split(
            r'\s+(?:and|with|or|behind|on|for|via|using)\s+',
            segment,
            flags=re.IGNORECASE,
        )
        result.extend(parts)

    return [t.strip() for t in result if t.strip()]


# Known technology pairs where one is a superset/compilation target
# of the other.  If user says "TypeScript" and architecture uses
# "JavaScript", that is NOT a substitution — TS compiles to JS.
_TECH_EQUIVALENTS: set[frozenset[str]] = {
    frozenset({"typescript", "javascript"}),
    frozenset({"dart", "flutter"}),
    frozenset({"c#", ".net"}),
    frozenset({"c#", "asp.net"}),
    frozenset({"c#", "asp.net core"}),
    frozenset({"kotlin", "android"}),
    frozenset({"swift", "ios"}),
    frozenset({"python", "cpython"}),
    frozenset({"julia", "julia lang"}),
}


def _are_equivalent(a: str, b: str) -> bool:
    """Check if two normalized tech names are equivalent (not substitutes)."""
    pair = frozenset({a, b})
    return pair in _TECH_EQUIVALENTS


def tech_sets_match(
    set_a: set[str],
    set_b: set[str],
    threshold: float = 0.6,
) -> tuple[bool, set[str], set[str]]:
    """
    Compare two normalized tech sets.

    Returns:
      (match, missing_in_b, extra_in_b)
      where missing_in_b = items in set_a not found in set_b
      and extra_in_b = items in set_b not found in set_a
    """
    missing = set_a - set_b
    extra = set_b - set_a

    # Fuzzy matching: if "aws fargate" is in one set and "fargate" in the other, match
    # Also check tech equivalents (e.g. TypeScript/JavaScript)
    fuzzy_missing = set()
    for m in missing:
        matched = False
        for e in extra:
            if m in e or e in m:
                matched = True
                break
            if _are_equivalent(m, e):
                matched = True
                break
        if not matched:
            fuzzy_missing.add(m)

    fuzzy_extra = set()
    for e in extra:
        matched = False
        for m in missing:
            if e in m or m in e:
                matched = True
                break
            if _are_equivalent(m, e):
                matched = True
                break
        if not matched:
            fuzzy_extra.add(e)

    return len(fuzzy_missing) == 0 and len(fuzzy_extra) == 0, fuzzy_missing, fuzzy_extra


# ============================================================
# Technology category classification
# ============================================================

# Semantic categories for technology comparison.
# Technologies in the SAME category can be substitutes.
# For example, OpenAI and Anthropic are both AI_PROVIDER.
TECH_CATEGORIES: dict[str, list[str]] = {
    "AI_PROVIDER": [
        "openai", "openai gpt-4", "openai gpt-3.5", "anthropic",
        "claude", "tensorflow", "pytorch", "huggingface",
        "langchain", "llm", "aws bedrock", "amazon bedrock",
        "google vertex ai", "azure openai",
    ],
    "PAYMENT_PROVIDER": [
        "stripe", "paypal", "chapa", "telebirr", "budpay",
        "paystack", "razorpay",
    ],
    "SMS_PROVIDER": [
        "twilio", "africas talking", "sendgrid", "vonage",
        "nexmo", "messagebird",
    ],
    "MAP_PROVIDER": [
        "google maps", "mapbox", "here maps", "leaflet",
        "openstreetmap",
    ],
    "DATABASE": [
        "postgresql", "mysql", "mongodb", "redis", "sqlite",
        "dynamodb", "supabase", "firestore", "cassandra",
        "mariadb", "couchdb", "sql server",
    ],
    "CLOUD_PROVIDER": [
        "aws", "gcp", "azure", "google cloud", "digitalocean",
        "heroku", "render", "vercel", "netlify",
    ],
    "HOSTING": [
        "docker", "containers", "kubernetes", "aws fargate", "aws ecs",
        "aws lambda", "google cloud run", "fly.io",
    ],
    "AUTH_PROVIDER": [
        "auth0", "clerk", "firebase auth", "supabase auth",
        "jwt", "oauth", "oauth2",
    ],
    "FRONTEND_FRAMEWORK": [
        "react", "next.js", "vue", "angular", "svelte",
        "flutter", "react native", "nuxt",
    ],
    "BACKEND_FRAMEWORK": [
        "node.js", "express", "fastapi", "django", "flask",
        "spring boot", "laravel", "rails", "asp.net core",
    ],
    "CI_CD": [
        "github actions", "gitlab ci", "aws codepipeline",
        "circleci", "jenkins",
    ],
    "TESTING": [
        "jest", "pytest", "vitest", "cypress", "playwright",
        "selenium",
    ],
}

# ============================================================
# DEVELOPMENT / VERSION-CONTROL TOOLS
# ============================================================
# These are legitimate user-selected technologies, but they are
# development/tooling infrastructure — NOT runtime architecture
# components. They should NOT cause architecture rejection when
# absent from the generated architecture's technology_stack.
DEV_TOOLS: set[str] = {
    "git", "github", "gitlab", "bitbucket",
    "github actions", "gitlab ci",
}


# Build reverse lookup: tech_name -> category
_TECH_TO_CATEGORY: dict[str, str] = {}
for _cat, _techs in TECH_CATEGORIES.items():
    for _t in _techs:
        _TECH_TO_CATEGORY[_t] = _cat


def classify_tech(tech_name: str) -> str:
    """Classify a technology into its semantic category.

    Uses exact name matching only — never substring matching.
    Returns the category name, or "OTHER" if unknown.
    """
    normalized = normalize_tech_name(tech_name)
    if not normalized:
        return "OTHER"

    # Exact match against known tech names
    if normalized in _TECH_TO_CATEGORY:
        return _TECH_TO_CATEGORY[normalized]

    # Try normalized name variants
    name_lower = tech_name.strip().lower()
    if name_lower in _TECH_TO_CATEGORY:
        return _TECH_TO_CATEGORY[name_lower]

    # No substring matching — too many false positives
    return "OTHER"


def find_substituted_technologies(
    user_techs: list[str],
    arch_techs: list[str],
) -> list[dict]:
    """
    Detect when the architecture uses a different technology in the
    same category as a user-selected technology.

    Returns a list of substitution detections:
    [
        {
            "category": "AI_PROVIDER",
            "user_techs": ["OpenAI API"],
            "arch_techs": ["Amazon Bedrock"],
            "substituted_with": ["amazon bedrock"],
            "severity": "contradiction"
        }
    ]
    """
    substitutions = []

    # Normalize all tech names for comparison.
    # Use normalize_tech_list which handles compound strings like
    # "React - Frontend" -> {"react"} and splits on " - ".
    user_norm_set = normalize_tech_list(user_techs)
    arch_norm_set = normalize_tech_list(arch_techs)

    # Build category maps using normalized names.
    # Map normalized name back to original for reporting.
    user_orig_map: dict[str, str] = {}
    for t in user_techs:
        n = normalize_tech_name(t)
        if n and len(n) > 1:
            user_orig_map[n] = t

    arch_orig_map: dict[str, str] = {}
    for t in arch_techs:
        # For compound strings like "React - Frontend", take the first token
        n = normalize_tech_name(t)
        if n and len(n) > 1:
            arch_orig_map[n] = t

    user_categories: dict[str, list[str]] = {}
    for norm_name in user_norm_set:
        orig = user_orig_map.get(norm_name, norm_name)
        cat = classify_tech(orig)
        if cat not in user_categories:
            user_categories[cat] = []
        user_categories[cat].append(orig)

    arch_categories: dict[str, list[str]] = {}
    for norm_name in arch_norm_set:
        orig = arch_orig_map.get(norm_name, norm_name)
        cat = classify_tech(orig)
        if cat not in arch_categories:
            arch_categories[cat] = []
        arch_categories[cat].append(orig)

    for cat, user_list in user_categories.items():
        if cat == "OTHER":
            continue
        arch_list = arch_categories.get(cat, [])
        if not arch_list:
            continue

        # Check if the architecture uses a DIFFERENT technology in this category
        user_cat_norm = {normalize_tech_name(t) for t in user_list}
        arch_cat_norm = {normalize_tech_name(t) for t in arch_list}

        if user_cat_norm != arch_cat_norm and user_cat_norm & arch_cat_norm != user_cat_norm:
            # User selected tech X, but arch uses tech Y in same category
            substituted = arch_cat_norm - user_cat_norm
            if substituted:
                substitutions.append({
                    "category": cat,
                    "user_techs": sorted(user_list),
                    "arch_techs": sorted(arch_list),
                    "substituted_with": sorted(substituted),
                    "severity": "contradiction",
                })

    return substitutions
