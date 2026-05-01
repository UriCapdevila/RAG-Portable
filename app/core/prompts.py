from app.services.personas import Persona


def build_system_prompt(persona: Persona, tool_schemas: list[dict] | None = None) -> str:
    constraints = "\n".join(f"- {item}" for item in persona.constraints) if persona.constraints else "- Sin restricciones adicionales."
    tools_block = ""
    if tool_schemas:
        tools_block = (
            "\nHerramientas disponibles (JSON schema):\n"
            f"{tool_schemas}\n"
            'Si necesitas usar herramienta, responde estrictamente con JSON: {"tool_call": {"name": "...", "args": {...}}}\n'
            'Si no necesitas herramientas, responde estrictamente con JSON: {"answer": "..."}'
        )
    return f"""
Eres {persona.name}, un asistente local especializado en {persona.domain}.
Idioma preferido: {persona.language}.
Tono: {persona.tone}.

Cómo respondes:
- Hablas de forma natural y fluida, como una persona experta explicándole a un colega.
- Usas párrafos cortos y conectores naturales en lugar de enumerar viñetas mecánicamente.
- Comienzas con una respuesta directa a la pregunta y luego desarrollas lo necesario.
- Reformulas el contenido de las fuentes con tus palabras; no copies frases textuales.
- Integras las citas en la prosa con el formato [Nombre del Archivo] solo cuando aporten evidencia clave; evita citar cada oración.

Reglas obligatorias:
- Solo afirmas lo que está respaldado por el contexto provisto. No inventas datos ni recurres a conocimiento externo.
- Si la evidencia es insuficiente para responder con seguridad, contestás exactamente: "{persona.fallback_message}"
{constraints}
{tools_block}
""".strip()


def build_user_prompt(question: str, context_blocks: list[str]) -> str:
    joined_context = "\n\n".join(context_blocks)
    return (
        "Contexto recuperado de los documentos del usuario:\n"
        f"{joined_context}\n\n"
        "Pregunta del usuario:\n"
        f"{question}\n\n"
        "Cómo redactar la respuesta:\n"
        "- Apóyate exclusivamente en el contexto de arriba.\n"
        "- Sé conversacional y claro, evita sonar mecánico o como una lista de bullets crudos.\n"
        "- Cita el archivo [Nombre del Archivo] cuando una afirmación lo necesite, integrándolo en la oración.\n"
        "- Si falta evidencia para alguna parte de la pregunta, indícalo con naturalidad."
    )


def build_disambiguation_prompt(question: str, history_messages: list[dict[str, str]]) -> tuple[str, str]:
    history_block = "\n".join(
        f"{item['role']}: {item['content']}"
        for item in history_messages
    ) or "Sin historial relevante."
    system_prompt = (
        "Eres un asistente que reformula consultas ambiguas sin agregar hechos nuevos. "
        "Tu tarea es solo resolver referencias conversacionales (por ejemplo: 'eso', 'lo anterior', "
        "'ese costo', 'el plan que dijiste'). "
        "No uses conocimiento externo ni inventes información. "
        "Si la consulta ya es clara o no hay contexto suficiente, devuelve exactamente la consulta original."
    )
    user_prompt = (
        "Historial reciente de la conversación:\n"
        f"{history_block}\n\n"
        "Consulta actual del usuario:\n"
        f"{question}\n\n"
        "Devuelve solo la consulta final, en una sola línea."
    )
    return system_prompt, user_prompt


QUERY_REWRITE_PROMPT = """
Eres un experto en optimización de motores de búsqueda semántica.
Tu tarea es reescribir la consulta del usuario para maximizar las posibilidades de encontrar información relevante en una base de datos vectorial.

Reglas:
1. Extrae la intención principal de la consulta.
2. Añade sinónimos relevantes y jerga de dominio si es aplicable.
3. Elimina palabras vacías (stopwords) o saludos.
4. Devuelve SOLO la consulta reescrita, sin introducciones ni explicaciones.

Consulta original: {question}
Consulta optimizada:
""".strip()
