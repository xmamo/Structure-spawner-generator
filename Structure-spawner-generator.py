# Structure spawner generator
# Copyright (C) 2016  Matteo Morena
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import inspect
import re
from decimal import Decimal

import mcplatform
from pymclevel import materials
from pymclevel.nbt import TAG_Compound, TAG_String, TAG_Int, TAG_List, TAG_Byte_Array, TAG_Short_Array, TAG_Int_Array, TAG_Byte, TAG_Short, TAG_Long, TAG_Float, TAG_Double
from pymclevel.schematic import MCSchematic

displayName = "Structure spawner generator"

inputs = (
	("Relative position", ("North", "East", "South", "West")),
	("Forward offset", 2),
	("Left offset", 0),
	("Up offset", 0),
	("Include air", False),
	("Include blocks", True),
	("Include null block data", False),
	("Include entities", False),
	("Include \"gamerule commandBlockOutput false\" command", True),
	("Include \"gamerule logAdminCommands false\" command", True),
	("Add initialization commands", False),
	("Add finalization commands", False),
	("Blocks to enqueue", ("string", "value=minecraft:sapling, minecraft:bed, minecraft:golden_rail, minecraft:detector_rail, minecraft:tallgrass, minecraft:deadbush, minecraft:piston_head, minecraft:piston_extension, minecraft:yellow_flower, minecraft:red_flower, minecraft:brown_mushroom, minecraft:red_mushroom, minecraft:torch, minecraft:fire, minecraft:redstone_wire, minecraft:wheat, minecraft:standing_sign, minecraft:wooden_door, minecraft:ladder, minecraft:rail, minecraft:wall_sign, minecraft:lever, minecraft:stone_pressure_plate, minecraft:iron_door, minecraft:wooden_pressure_plate, minecraft:unlit_redstone_torch, minecraft:redstone_torch, minecraft:stone_button, minecraft:snow_layer, minecraft:cactus, minecraft:reeds, minecraft:portal, minecraft:cake, minecraft:unpowered_repeater, minecraft:powered_repeater, minecraft:trapdoor, minecraft:pumpkin_stem, minecraft:melon_stem, minecraft:vine, minecraft:waterlily, minecraft:nether_wart, minecraft:end_portal, minecraft:cocoa, minecraft:tripwire_hook, minecraft:flower_pot, minecraft:carrots, minecraft:potatoes, minecraft:wooden_button, minecraft:light_weighted_pressure_plate, minecraft:heavy_weighted_pressure_plate, minecraft:unpowered_comparator, minecraft:powered_comparator, minecraft:activator_rail, minecraft:iron_trapdoor, minecraft:carpet, minecraft:double_plant, minecraft:standing_banner, minecraft:wall_banner, minecraft:spruce_door, minecraft:birch_door, minecraft:jungle_door, minecraft:acacia_door, minecraft:dark_oak_door, minecraft:chorus_plant, minecraft:chorus_flower, minecraft:beetroots")),
	("NBT tags to ignore", ("string", "value=Pos, Motion, Rotation, FallDIstance, Fire, Air, OnGround, Dimension, PortalCooldown, UUIDMost, UUIDLeast, HurtTime, HurtByTimestamp, DeathTime, EggLayTime, Fuse, Lifetime, PlayerSpawned, EatingHaystack, wasOnGround, HurtBy, life, inGround, ownerName, Age, Thrower, PushX, PushZ, TransferCooldown, SuccessCount, LastOutput, conditionMet, OwnerUUIDMost, OwnerUUIDLeast, Life, Levels, BrewTime, OutputSignal, CookTime, CookTimeTotal")),
	("Save the command to a file instead of to a Command Block", False),
	("Ignore maximum Command Block command length", False)
)


def perform(level, box, options):
	editor = inspect.stack()[1][0].f_locals.get("self", None).editor

	if options["Relative position"] == "North":
		execution_center = ((box.minx + box.maxx) // 2 + options["Left offset"], box.miny - options["Up offset"] + 2, box.maxz + options["Forward offset"] - 1)
	elif options["Relative position"] == "East":
		execution_center = (box.minx - options["Forward offset"], box.miny - options["Up offset"] + 2, (box.minz + box.maxz) // 2 + options["Left offset"])
	elif options["Relative position"] == "South":
		execution_center = ((box.minx + box.maxx) // 2 - options["Left offset"], box.miny - options["Up offset"] + 2, box.minz - options["Forward offset"])
	if options["Relative position"] == "West":
		execution_center = (box.maxx + options["Forward offset"] - 1, box.miny - options["Up offset"] + 2, (box.minz + box.maxz) // 2 - options["Left offset"])
	include_air = options["Include air"]
	include_blocks = options["Include blocks"]
	include_null_block_data = options["Include null block data"]
	include_entities = options["Include entities"]
	include_commandblockoutput_command = options["Include \"gamerule commandBlockOutput false\" command"]
	include_logadmincommands_command = options["Include \"gamerule logAdminCommands false\" command"]
	add_initialization_commands = options["Add initialization commands"]
	add_finalization_commands = options["Add finalization commands"]
	block_names_to_enqueue = re.split("\\s*,\\s*", options["Blocks to enqueue"])
	blocks_to_enqueue = []
	for block_id in xrange(0, len(materials.block_map) - 1):
		if materials.block_map[block_id] in block_names_to_enqueue:
			blocks_to_enqueue.append(block_id)
	nbt_tags_to_ignore = re.split("\\s*,\\s*", options["NBT tags to ignore"]) + ["x", "y", "z"]
	save_command_to_file = options["Save the command to a file instead of to a Command Block"]
	ignore_maximum_command_block_command_length = options["Ignore maximum Command Block command length"]
	add_credits = True

	command = "summon minecraft:falling_block ~ ~1 ~ {id:\"minecraft:falling_block\",Block:\"minecraft:redstone_block\",Time:1,Passengers:[{id:\"minecraft:falling_block\",Block:\"minecraft:activator_rail\",Time:1,Passengers:["
	unformatted_command = command
	first_element = True

	if include_commandblockoutput_command:
		command_part = "{id:\"minecraft:commandblock_minecart\",Command:\"gamerule commandBlockOutput false\"}"
		command += "\n\t" + command_part
		unformatted_command += command_part
		first_element = False

	if include_logadmincommands_command:
		if not first_element:
			command += ","
			unformatted_command += ","
		first_element = False
		command_part = "{id:\"minecraft:commandblock_minecart\",Command:\"gamerule logAdminCommands false\"}"
		command += "\n\t" + command_part
		unformatted_command += command_part

	if add_initialization_commands:
		file_name = mcplatform.askOpenFile("Select the text file containing the initialization commands...", False, ["txt"])
		if file_name is not None:
			input = open(file_name)
			if input is not None:
				for line in input.read().splitlines():
					if not first_element:
						command += ","
						unformatted_command += ","
					first_element = False
					command_part = "{id:\"minecraft:commandblock_minecart\",Command:\"" + escape_string(line) + "\"}"
					command += "\n\t" + command_part
					unformatted_command += command_part
				input.close()

	if include_blocks:
		if include_air:
			air_blocks = []
			for x in xrange(box.minx, box.maxx):
				air_blocks.append([])
				for y in xrange(box.miny, box.maxy):
					air_blocks[x - box.minx].append([])
					for z in xrange(box.minz, box.maxz):
						air_blocks[x - box.minx][y - box.miny].append(True)
			for cuboid in subdivide_in_cuboids(air_blocks, 32768, False, True, False):
				if not first_element:
					command += ","
					unformatted_command += ","
				first_element = False
				if volume(cuboid[0][0], cuboid[0][1], cuboid[0][2], cuboid[1][0], cuboid[1][1], cuboid[1][2]) == 1:
					command_part = "{id:\"minecraft:commandblock_minecart\",Command:\"setblock ~" + str(cuboid[0][0] + box.minx - execution_center[0]) + " ~" + str(cuboid[0][1] + box.miny - execution_center[1]) + " ~" + str(cuboid[0][2] + box.minz - execution_center[2]) + " minecraft:air"
				else:
					command_part = "{id:\"minecraft:commandblock_minecart\",Command:\"fill ~" + str(cuboid[0][0] + box.minx - execution_center[0]) + " ~" + str(cuboid[0][1] + box.miny - execution_center[1]) + " ~" + str(cuboid[0][2] + box.minz - execution_center[2]) + " ~" + str(cuboid[1][0] + box.minx - execution_center[0]) + " ~" + str(cuboid[1][1] + box.miny - execution_center[1]) + " ~" + str(cuboid[1][2] + box.minz - execution_center[2]) + " minecraft:air"
				if include_null_block_data:
					command_part += " 0"
				command_part += "\"}"
				command += "\n\t" + command_part
				unformatted_command += command_part

		blocks = []
		for x in xrange(box.minx, box.maxx):
			blocks.append([])
			for y in xrange(box.miny, box.maxy):
				blocks[x - box.minx].append([])
				for z in xrange(box.minz, box.maxz):
					blocks[x - box.minx][y - box.miny].append((level.blockAt(x, y, z), level.blockDataAt(x, y, z), level.tileEntityAt(x, y, z)))
		enqueued = []
		for x in xrange(0, len(blocks)):
			for y in xrange(0, len(blocks[x])):
				for z in xrange(0, len(blocks[x][y])):
					block = blocks[x][y][z]
					if block[0] >= 1:
						for cuboid in subdivide_in_cuboids(blocks, 32768, False, (block[0], block[1], block[2]), (-1, 0, None)):
							if block[0] != 0 or (block[0] == 0 and include_air):
								if volume(cuboid[0][0], cuboid[0][1], cuboid[0][2], cuboid[1][0], cuboid[1][1], cuboid[1][2]) == 1:
									command_part = "{id:\"minecraft:commandblock_minecart\",Command:\"setblock ~" + str(cuboid[0][0] + box.minx - execution_center[0]) + " ~" + str(cuboid[0][1] + box.miny - execution_center[1]) + " ~" + str(cuboid[0][2] + box.minz - execution_center[2]) + " " + materials.block_map[block[0]]
								else:
									command_part = "{id:\"minecraft:commandblock_minecart\",Command:\"fill ~" + str(cuboid[0][0] + box.minx - execution_center[0]) + " ~" + str(cuboid[0][1] + box.miny - execution_center[1]) + " ~" + str(cuboid[0][2] + box.minz - execution_center[2]) + " ~" + str(cuboid[1][0] + box.minx - execution_center[0]) + " ~" + str(cuboid[1][1] + box.miny - execution_center[1]) + " ~" + str(cuboid[1][2] + box.minz - execution_center[2]) + " " + materials.block_map[block[0]]
								if include_null_block_data or block[1] != 0 or (block[1] == 0 and block[2] is not None):
									command_part += " " + str(block[1])
								if block[2] is not None:
									command_part += " replace " + escape_string(nbt_to_string(block[2], nbt_tags_to_ignore))
								command_part += "\"}"
								if block[0] not in blocks_to_enqueue:
									if not first_element:
										command += ","
										unformatted_command += ","
									first_element = False
									command += "\n\t" + command_part
									unformatted_command += command_part
								else:
									enqueued.append(command_part)
		for enqueued_command in enqueued:
			if not first_element:
				command += ","
				unformatted_command += ","
			first_element = False
			command += "\n\t" + enqueued_command
			unformatted_command += enqueued_command

	if include_entities:
		for (chunk, slices, point) in level.getChunkSlices(box):
			for entity in chunk.Entities:
				entity_x = entity["Pos"][0].value
				entity_y = entity["Pos"][1].value
				entity_z = entity["Pos"][2].value
				if (entity_x, entity_y, entity_z) in box:
					if not first_element:
						command += ","
						unformatted_command += ","
					first_element = False
					command_part = "{id:\"minecraft:commandblock_minecart\",Command:\"summon " + str(entity["id"].value) + " ~" + str((Decimal(entity_x - execution_center[0]) - Decimal("0.5")).normalize()) + " ~" + str((Decimal(entity_y - execution_center[1]) - Decimal("0.0625")).normalize()) + " ~" + str((Decimal(entity_z - execution_center[2]) - Decimal("0.5")).normalize()) + " " + escape_string(nbt_to_string(entity, nbt_tags_to_ignore)) + "\"}"
					command += "\n\t" + command_part
					unformatted_command += command_part

	if add_finalization_commands:
		file_name = mcplatform.askOpenFile("Select the text file containing the finalization commands...", False, ["txt"])
		if file_name is not None:
			input = open(file_name)
			if input is not None:
				for line in input.read().splitlines():
					if not first_element:
						command += ","
						unformatted_command += ","
					first_element = False
					command_part = "{id:\"minecraft:commandblock_minecart\",Command:\"" + escape_string(line) + "\"}"
					command += "\n\t" + command_part
					unformatted_command += command_part
				input.close()

	if add_credits:
		if not first_element:
			command += ","
			unformatted_command += ","
		first_element = False
		command_part = "{id:\"minecraft:commandblock_minecart\",Command:\"tellraw @p {\\\"text\\\":\\\"Generated with Mamo's \\\",\\\"color\\\":\\\"yellow\\\",\\\"extra\\\":[{\\\"text\\\":\\\"Structure spawner generator\\\",\\\"color\\\":\\\"blue\\\",\\\"clickEvent\\\":{\\\"action\\\":\\\"open_url\\\",\\\"value\\\":\\\"https://github.com/xMamo/Structure-spawner-generator\\\"},\\\"hoverEvent\\\":{\\\"action\\\":\\\"show_text\\\",\\\"value\\\":\\\"Click here if you want this filter too!\\\"}},\\\".\\\"]}\"}"
		command += "\n\t" + command_part
		unformatted_command += command_part

	if not first_element:
		command += ","
		unformatted_command += ","
	command_part = "{id:\"minecraft:commandblock_minecart\",Command:\"setblock ~ ~1 ~ minecraft:command_block 0 replace {auto:1b,Command:\\\"fill ~ ~-3 ~ ~ ~ ~ minecraft:air"
	if include_null_block_data:
		command_part += " 0"
	command_part += "\\\"}\"}"
	command += "\n\t" + command_part
	unformatted_command += command_part
	command_part = "{id:\"minecraft:commandblock_minecart\",Command:\"kill @e[type=minecraft:commandblock_minecart,r=0]\"}\n]}]}"
	command += ",\n\t" + command_part
	unformatted_command += "," + command_part

	if not ignore_maximum_command_block_command_length and len(unformatted_command) > 32767:
		editor.Notify("Unfortunately no command could be generated, as it would be longer than the Command Block command length limit of 32767 characters.")
		return

	command_output = None
	if save_command_to_file:
		output_file = mcplatform.askSaveFile(None, "Select the text file to wich you want to save the command...", "command.txt", "Text file (*.txt)\0*.txt\0", None)
		if output_file is not None:
			command_output = open(output_file, "w")

	if save_command_to_file and command_output is not None:
		command_output.write(command)
		command_output.flush()
		command_output.close()
	else:
		schematic = MCSchematic((1, 1, 1), None, None, level.materials)
		schematic.setBlockAt(0, 0, 0, 137)
		schematic.setBlockDataAt(0, 0, 0, 0)
		command_block = TAG_Compound()
		command_block["id"] = TAG_String("Control")
		command_block["x"] = TAG_Int(0)
		command_block["y"] = TAG_Int(0)
		command_block["z"] = TAG_Int(0)
		command_block["CustomName"] = TAG_String("@")
		command_block["Command"] = TAG_String(unformatted_command)
		command_block["SuccessCount"] = TAG_Int(0)
		command_block["TrackOutput"] = TAG_Byte(1)
		command_block["powered"] = TAG_Byte(0)
		command_block["auto"] = TAG_Byte(0)
		command_block["conditionMet"] = TAG_Byte(0)
		schematic.addTileEntity(command_block)
		editor.addCopiedSchematic(schematic)


def escape_string(string):
	return string.replace("\\", "\\\\").replace("\"", "\\\"")


def volume(x1, y1, z1, x2, y2, z2):
	return (x2 - x1 + 1) * (y2 - y1 + 1) * (z2 - z1 + 1)


def subdivide_in_cuboids(array, max_volume, use_temp_copy, compare_with, replacement):
	if use_temp_copy:
		return __subdivide_in_cuboids(list(array), max_volume, compare_with, replacement)
	else:
		return __subdivide_in_cuboids(array, max_volume, compare_with, replacement)


def __subdivide_in_cuboids(array, max_volume, compare_with, replacement):
	cuboids = []

	for x1 in xrange(0, len(array)):
		for y1 in xrange(0, len(array[x1])):
			for z1 in xrange(0, len(array[x1][y1])):
				if array[x1][y1][z1] == compare_with:
					x2 = x1
					while x2 < len(array) and array[x2][y1][z1] == compare_with:
						x2 += 1
					x2 -= 1
					while volume(x1, y1, z1, x2, y1, z1) > max_volume:
						x2 -= 1

					y2 = len(array[x1]) - 1
					for x in xrange(x1, x2 + 1):
						y = y1
						while y <= y2 and array[x][y][z1] == compare_with:
							y += 1
						y -= 1
						if y < y2:
							y2 = y
					while volume(x1, y1, z1, x2, y2, z1) > max_volume:
						y2 -= 1

					z2 = len(array[x1][y1]) - 1
					for x in xrange(x1, x2 + 1):
						for y in xrange(y1, y2 + 1):
							z = z1
							while z <= z2 and array[x][y][z] == compare_with:
								z += 1
							z -= 1
							if z < z2:
								z2 = z
					while volume(x1, y1, z1, x2, y2, z2) > max_volume:
						z2 -= 1

					cuboid = ((x1, y1, z1), (x2, y2, z2))
					cuboids.append(cuboid)

					for x in xrange(x1, x2 + 1):
						for y in xrange(y1, y2 + 1):
							for z in xrange(z1, z2 + 1):
								array[x][y][z] = replacement

	return cuboids


def nbt_to_string(nbt, ignored_tags):
	string = ""
	if type(nbt) is TAG_Compound:
		string += "{"
		first_element = True
		for tag in nbt.keys():
			if tag != "" and tag in ignored_tags:
				continue
			if not first_element:
				string += ","
			first_element = False
			if tag != "":
				string += tag + ":"
			string += nbt_to_string(nbt[tag], ignored_tags)
		string += "}"
	elif type(nbt) in [TAG_List, TAG_Byte_Array, TAG_Short_Array, TAG_Int_Array]:
		string += "["
		first_element = True
		for tag in xrange(0, len(nbt)):
			if not first_element:
				string += ","
			first_element = False
			string += nbt_to_string(nbt[tag], ignored_tags)
		string += "]"
	elif type(nbt) is TAG_String:
		string += "\"" + escape_string(nbt.value) + "\""
	elif type(nbt) is TAG_Byte:
		string += str(nbt.value) + "b"
	elif type(nbt) is TAG_Short:
		string += str(nbt.value) + "s"
	elif type(nbt) is TAG_Int:
		string += str(nbt.value)
	elif type(nbt) is TAG_Long:
		string += str(nbt.value) + "l"
	elif type(nbt) is TAG_Float:
		string += str(nbt.value) + "f"
	elif type(nbt) is TAG_Double:
		string += str(nbt.value) + "d"
	return string