def create_gameboy_button_tool(name: str) -> dict:
    """Create an OpenAI function tool for a Game Boy button press."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": f"Press the {name} button on the Game Boy",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }


def tool_to_pyboy_button(tool_name: str) -> str:
    match tool_name:
        case "press_a":
            return "a"
        case "press_b":
            return "b"
        case "press_start":
            return "start"
        case "press_select":
            return "select"
        case "press_up":
            return "up"
        case "press_down":
            return "down"
        case "press_left":
            return "left"
        case "press_right":
            return "right"
        case _:
            raise ValueError(f"Invalid tool name: {tool_name}")


ALL_GB_BUTTONS = [
    create_gameboy_button_tool("press_a"),
    create_gameboy_button_tool("press_b"),
    create_gameboy_button_tool("press_start"),
    create_gameboy_button_tool("press_select"),
    create_gameboy_button_tool("press_up"),
    create_gameboy_button_tool("press_down"),
    create_gameboy_button_tool("press_left"),
    create_gameboy_button_tool("press_right"),
]
