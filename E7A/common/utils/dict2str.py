def dict2str(d: dict, indent: int = 4):
    """Convert a dictionary to a formatted string with indentation."""
    def parse_dict(d: dict, indent: int) -> str:
        items = []
        for key, value in d.items():
            if isinstance(value, dict):
                items.append(f"{' ' * indent}{key}:{{")   # 字典名、{
                items.append(f"{parse_dict(value, indent * 2)}")    # 字典内容
                items.append(f"{' ' * indent}}}")   # 结尾}
            else:
                type_info = type(value).__name__
                quotation = "\"" if isinstance(value, str) else ""
                items.append(f"{' ' * indent}{key}: {type_info} = {quotation}{value}{quotation}")
        return "\n".join(items)

    return "{\n" + parse_dict(d, indent) + "\n}"
