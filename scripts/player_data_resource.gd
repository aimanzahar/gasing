extends Resource
class_name PlayerData

@export var multiplayer_id: int = 0
@export var display_name: String = "Player"
@export var steam_id: int = -1
@export var color: Color = Color.WHITE

var _custom_variables: Array[String]: get = _get_custom_variables # Lists the resource custom variable names

static func from_dict(dict: Dictionary) -> PlayerData:
	var player_data := PlayerData.new()
	var raw_id: Variant = dict.get("multiplayer_id", 0)
	if raw_id is int:
		player_data.multiplayer_id = maxi(raw_id, 0)
	var raw_name: Variant = dict.get("display_name", "Player")
	if raw_name is String:
		player_data.display_name = raw_name.replace("\n", " ").replace("\r", " ").replace("\t", " ").strip_edges().left(32)
		if player_data.display_name.is_empty():
			player_data.display_name = "Player"
	var raw_steam_id: Variant = dict.get("steam_id", -1)
	if raw_steam_id is int:
		player_data.steam_id = maxi(raw_steam_id, -1)
	var raw_color: Variant = dict.get("color", Color.WHITE)
	if raw_color is Color and is_finite(raw_color.r) and is_finite(raw_color.g) and is_finite(raw_color.b) and is_finite(raw_color.a):
		player_data.color = Color(clampf(raw_color.r, 0.0, 1.0), clampf(raw_color.g, 0.0, 1.0), clampf(raw_color.b, 0.0, 1.0), clampf(raw_color.a, 0.0, 1.0))
	return player_data

static func apply_data_to_node(data: PlayerData, node: Node) -> void:
	if not data: return
	var id := data.multiplayer_id
	node.name = str(id)
	node.set_multiplayer_authority(id)
	if node.get("player_data") is PlayerData:
		node.set("player_data", data)

func to_dict() -> Dictionary:
	var dict := {}
	for var_name in _custom_variables:
		var value: Variant = self.get(var_name)
		if value != null: dict.set(var_name,value)
	return dict

func _setup_custom_variables() -> void:
	var new_custom_variables: Array[String]
	var script: Script = self.get_script()
	if not script: return
	for property in script.get_script_property_list():
		if property.usage and PROPERTY_USAGE_SCRIPT_VARIABLE:
			var prop_name := str(property.name).strip_edges()
			if prop_name.begins_with("_") or prop_name in new_custom_variables: continue
			new_custom_variables.append(prop_name)
	_custom_variables = new_custom_variables

func _get_custom_variables() -> Array[String]:
	if _custom_variables.is_empty(): _setup_custom_variables()
	return _custom_variables
