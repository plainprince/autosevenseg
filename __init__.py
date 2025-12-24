"""
Auto7Seg - Automating seven segment clocks.
Author: plainprince
Version: 1.0.0
"""

import bpy
from bpy.props import (
    PointerProperty,
    FloatProperty,
    IntProperty,
    EnumProperty,
    FloatVectorProperty,
    BoolProperty,
)
from bpy.types import PropertyGroup, Panel, Operator
from bpy_extras import anim_utils
from mathutils import Vector, Euler
import math

bl_info = {
    "name": "Auto7Seg",
    "author": "plainprince",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Auto7Seg",
    "description": "Automate creating seven segment clocks",
    "category": "3D View",
}

# Standard 7-segment digit patterns
# Segments: A=top, B=top-right, C=bottom-right, D=bottom, E=bottom-left, F=top-left, G=middle
#  AAA
# F   B
#  GGG
# E   C
#  DDD
DIGIT_PATTERNS = {
    0: [True, True, True, True, True, True, False],      # A,B,C,D,E,F on; G off
    1: [False, True, True, False, False, False, False],  # B,C on
    2: [True, True, False, True, True, False, True],     # A,B,D,E,G on
    3: [True, True, True, True, False, False, True],     # A,B,C,D,G on
    4: [False, True, True, False, False, True, True],    # B,C,F,G on
    5: [True, False, True, True, False, True, True],     # A,C,D,F,G on
    6: [True, False, True, True, True, True, True],      # A,C,D,E,F,G on
    7: [True, True, True, False, False, False, False],   # A,B,C on
    8: [True, True, True, True, True, True, True],       # All on
    9: [True, True, True, True, False, True, True],      # A,B,C,D,F,G on
}

SEGMENT_NAMES = ['A', 'B', 'C', 'D', 'E', 'F', 'G']


class Auto7SegProperties(PropertyGroup):
    """Property group storing all Auto7Seg settings"""
    
    # Segment object references (A-G)
    segment_a: PointerProperty(
        name="Segment A (Top)",
        type=bpy.types.Object,
        description="Top horizontal segment"
    )
    segment_b: PointerProperty(
        name="Segment B (Top-Right)",
        type=bpy.types.Object,
        description="Top-right vertical segment"
    )
    segment_c: PointerProperty(
        name="Segment C (Bottom-Right)",
        type=bpy.types.Object,
        description="Bottom-right vertical segment"
    )
    segment_d: PointerProperty(
        name="Segment D (Bottom)",
        type=bpy.types.Object,
        description="Bottom horizontal segment"
    )
    segment_e: PointerProperty(
        name="Segment E (Bottom-Left)",
        type=bpy.types.Object,
        description="Bottom-left vertical segment"
    )
    segment_f: PointerProperty(
        name="Segment F (Top-Left)",
        type=bpy.types.Object,
        description="Top-left vertical segment"
    )
    segment_g: PointerProperty(
        name="Segment G (Middle)",
        type=bpy.types.Object,
        description="Middle horizontal segment"
    )
    
    # Transformation mode
    transform_mode: EnumProperty(
        name="Transform Mode",
        items=[
            ('LOCAL_ROTATION', "Local Rotation", "Use local rotation for on/off states"),
            ('GLOBAL_ROTATION', "Global Rotation", "Use global (world) rotation for on/off states"),
            ('LOCAL_LOCATION', "Local Location", "Use local location for on/off states"),
            ('GLOBAL_LOCATION', "Global Location", "Use global (world) location for on/off states"),
            ('SCALE', "Scale", "Use scale for on/off states"),
        ],
        default='LOCAL_ROTATION',
        description="Transformation type for segment on/off states"
    )
    
    # On state values
    on_local_rotation: FloatVectorProperty(
        name="On Local Rotation",
        subtype='EULER',
        default=(math.radians(180), 0.0, 0.0),
        description="Local rotation when segment is ON"
    )
    on_global_rotation: FloatVectorProperty(
        name="On Global Rotation",
        subtype='EULER',
        default=(math.radians(180), 0.0, 0.0),
        description="Global rotation when segment is ON"
    )
    on_local_location: FloatVectorProperty(
        name="On Local Location",
        subtype='TRANSLATION',
        default=(0.0, 0.0, 0.0),
        description="Local location when segment is ON"
    )
    on_global_location: FloatVectorProperty(
        name="On Global Location",
        subtype='TRANSLATION',
        default=(0.0, 0.0, 0.0),
        description="Global location when segment is ON"
    )
    on_scale: FloatVectorProperty(
        name="On Scale",
        subtype='XYZ',
        default=(1.0, 1.0, 1.0),
        description="Scale when segment is ON"
    )
    
    # Off state values
    off_local_rotation: FloatVectorProperty(
        name="Off Local Rotation",
        subtype='EULER',
        default=(0.0, 0.0, 0.0),
        description="Local rotation when segment is OFF"
    )
    off_global_rotation: FloatVectorProperty(
        name="Off Global Rotation",
        subtype='EULER',
        default=(0.0, 0.0, 0.0),
        description="Global rotation when segment is OFF"
    )
    off_local_location: FloatVectorProperty(
        name="Off Local Location",
        subtype='TRANSLATION',
        default=(0.0, 0.0, 0.0),
        description="Local location when segment is OFF"
    )
    off_global_location: FloatVectorProperty(
        name="Off Global Location",
        subtype='TRANSLATION',
        default=(0.0, 0.0, 0.0),
        description="Global location when segment is OFF"
    )
    off_scale: FloatVectorProperty(
        name="Off Scale",
        subtype='XYZ',
        default=(0.0, 0.0, 0.0),
        description="Scale when segment is OFF"
    )
    
    # Timing settings
    time_unit: EnumProperty(
        name="Time Unit",
        items=[
            ('FRAMES', "Frames", "Measure time in frames"),
            ('SECONDS', "Seconds", "Measure time in seconds"),
        ],
        default='FRAMES',
        description="Unit for timing values"
    )
    
    speed: FloatProperty(
        name="Speed",
        default=24.0,
        min=0.1,
        description="Duration between digit changes (in selected unit)"
    )
    
    switching_speed: FloatProperty(
        name="Switching Speed",
        default=5.0,
        min=0.0,
        description="Duration for segment transition animation (in selected unit)"
    )
    
    # Count mode settings
    count_mode: EnumProperty(
        name="Count Mode",
        items=[
            ('COUNT_UP', "Count Up", "Count from 0 to 9"),
            ('COUNT_DOWN', "Count Down", "Count from 9 to 0"),
            ('COUNT_FROM_TO', "Count From-To", "Count between specified values"),
        ],
        default='COUNT_UP',
        description="Counting direction/mode"
    )
    
    count_from: IntProperty(
        name="From",
        default=0,
        min=0,
        max=9,
        description="Starting digit for count"
    )
    
    count_to: IntProperty(
        name="To",
        default=9,
        min=0,
        max=9,
        description="Ending digit for count"
    )
    
    cyclic: BoolProperty(
        name="Cyclic",
        default=True,
        description="Automatically loop back to the first digit at the end"
    )
    
    def all_segments_assigned(self):
        """Check if all 7 segments have been assigned"""
        return all([
            self.segment_a,
            self.segment_b,
            self.segment_c,
            self.segment_d,
            self.segment_e,
            self.segment_f,
            self.segment_g,
        ])
    
    def get_segments(self):
        """Return list of segment objects in order A-G"""
        return [
            self.segment_a,
            self.segment_b,
            self.segment_c,
            self.segment_d,
            self.segment_e,
            self.segment_f,
            self.segment_g,
        ]


class AUTO7SEG_OT_set_to_active(Operator):
    """Copy transformation value from active object"""
    bl_idname = "auto7seg.set_to_active"
    bl_label = "Set to Active"
    bl_options = {'REGISTER', 'UNDO'}
    
    property_name: bpy.props.StringProperty(name="Property Name")
    axis: IntProperty(name="Axis Index", default=0)
    
    def execute(self, context):
        props = context.scene.auto7seg
        active = context.active_object
        
        if not active:
            self.report({'WARNING'}, "No active object selected")
            return {'CANCELLED'}
        
        # Get the value from active object based on property name
        value = None
        
        if self.property_name == 'on_local_rotation':
            value = active.rotation_euler[self.axis]
        elif self.property_name == 'off_local_rotation':
            value = active.rotation_euler[self.axis]
        elif self.property_name == 'on_global_rotation':
            value = active.matrix_world.to_euler('XYZ')[self.axis]
        elif self.property_name == 'off_global_rotation':
            value = active.matrix_world.to_euler('XYZ')[self.axis]
        elif self.property_name == 'on_local_location':
            value = active.location[self.axis]
        elif self.property_name == 'off_local_location':
            value = active.location[self.axis]
        elif self.property_name == 'on_global_location':
            value = active.matrix_world.translation[self.axis]
        elif self.property_name == 'off_global_location':
            value = active.matrix_world.translation[self.axis]
        elif self.property_name == 'on_scale':
            value = active.scale[self.axis]
        elif self.property_name == 'off_scale':
            value = active.scale[self.axis]
        
        if value is not None:
            # Get current vector and update the specific axis
            current = list(getattr(props, self.property_name))
            current[self.axis] = value
            setattr(props, self.property_name, current)
            return {'FINISHED'}
        
        return {'CANCELLED'}


class AUTO7SEG_OT_generate_animation(Operator):
    """Generate keyframe animation for the seven segment display"""
    bl_idname = "auto7seg.generate_animation"
    bl_label = "Generate Animation"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        props = context.scene.auto7seg
        return props.all_segments_assigned()
    
    def execute(self, context):
        props = context.scene.auto7seg
        scene = context.scene
        fps = scene.render.fps
        
        # Convert timing to frames
        if props.time_unit == 'SECONDS':
            speed_frames = int(props.speed * fps)
            switch_frames = int(props.switching_speed * fps)
        else:
            speed_frames = int(props.speed)
            switch_frames = int(props.switching_speed)
        
        # Determine digit sequence
        if props.count_mode == 'COUNT_UP':
            digits = list(range(0, 10))
        elif props.count_mode == 'COUNT_DOWN':
            digits = list(range(9, -1, -1))
        else:  # COUNT_FROM_TO
            start = props.count_from
            end = props.count_to
            if start <= end:
                digits = list(range(start, end + 1))
            else:
                digits = list(range(start, end - 1, -1))
        
        segments = props.get_segments()
        print(f"Auto7Seg: Processing {len(digits)} digits for segments: {[s.name if s else 'None' for s in segments]}")
        
        # Get on/off values based on transform mode
        mode = props.transform_mode
        if mode == 'LOCAL_ROTATION':
            # Store as tuples for easier handling
            on_values_tuple = tuple(props.on_local_rotation)
            off_values_tuple = tuple(props.off_local_rotation)
            data_path = 'rotation_euler'
        elif mode == 'GLOBAL_ROTATION':
            on_values_tuple = tuple(props.on_global_rotation)
            off_values_tuple = tuple(props.off_global_rotation)
            data_path = 'rotation_euler'
        elif mode == 'LOCAL_LOCATION':
            on_values = Vector(props.on_local_location)
            off_values = Vector(props.off_local_location)
            data_path = 'location'
        elif mode == 'GLOBAL_LOCATION':
            on_values = Vector(props.on_global_location)
            off_values = Vector(props.off_global_location)
            data_path = 'location'
        else:  # SCALE
            on_values = Vector(props.on_scale)
            off_values = Vector(props.off_scale)
            data_path = 'scale'
        
        current_frame = scene.frame_start
        
        
        # Helper function to apply rotation to a segment
        def apply_rotation(segment, target_tuple, mode):
            try:
                # Ensure we're in object mode and using XYZ Euler rotation mode
                if segment.rotation_mode != 'XYZ':
                    segment.rotation_mode = 'XYZ'
                
                target_x = target_tuple[0]
                target_y = target_tuple[1]
                target_z = target_tuple[2]
                
                if mode == 'LOCAL_ROTATION':
                    # Modify all 3 axes - but intelligently.
                    # For the main use case (7-segment), we usually only animate X.
                    # The user might have base rotations on Y or Z (e.g. -90) that must be preserved.
                    # If the Target Y/Z are 0 (default), we assume we should preserve the object's current Y/Z.
                    
                    current_rot = segment.rotation_euler
                    
                    # Use target X (absolute)
                    new_x = target_x
                    
                    # Use target Y if it's non-zero, otherwise preserve current Y
                    # (This is a heuristic to support the common case of "only animate X" while allowing custom Y/Z if specified)
                    # Note: A safer approach is strictly: X comes from UI, Y/Z preserved.
                    # Given the user's specific setup with -90 Y segments, preserving is key.
                    
                    # Let's strictly preserve Y and Z for LOCAL_ROTATION if target is 0? 
                    # Or better: Just preserve Y and Z always, assuming the UI controls the "Active" axis (X).
                    # But the UI shows X, Y, Z inputs.
                    
                    # Compromise: If the UI inputs for Y and Z are 0 (Off) and 0 (On), we preserve.
                    # If they are used (non-zero), we use them.
                    
                    use_y = target_y
                    if props.on_local_rotation[1] == 0 and props.off_local_rotation[1] == 0:
                         use_y = current_rot.y
                         
                    use_z = target_z
                    if props.on_local_rotation[2] == 0 and props.off_local_rotation[2] == 0:
                         use_z = current_rot.z
                    
                    segment.rotation_euler = Euler((new_x, use_y, use_z), 'XYZ')
                    
                else:  # GLOBAL_ROTATION
                    # ... (Global logic)
                    target_world = Euler(target_tuple, 'XYZ')
                    if segment.parent:
                        parent_inv = segment.parent.matrix_world.inverted()
                        target_matrix = target_world.to_matrix().to_4x4()
                        local_matrix = parent_inv @ target_matrix
                        segment.rotation_euler = local_matrix.to_euler('XYZ')
                    else:
                        segment.rotation_euler = target_world
            except Exception as e:
                print(f"Auto7Seg Error applying rotation to {segment.name}: {e}")
        
        # Helper function to apply location/scale to a segment
        def apply_transform(segment, final_values, mode):
            if mode in ('LOCAL_LOCATION', 'GLOBAL_LOCATION'):
                segment.location = final_values
            else:  # SCALE
                segment.scale = final_values
        
        # Helper function to get channelbag for Blender 5.0 API
        def get_channelbag(obj):
            """Get the ActionChannelbag for an object's action (Blender 5.0 API)"""
            if not obj.animation_data or not obj.animation_data.action:
                return None
            
            action = obj.animation_data.action
            action_slot = obj.animation_data.action_slot
            
            if action_slot is None:
                return None
            
            try:
                channelbag = anim_utils.action_get_channelbag_for_slot(action, action_slot)
                return channelbag
            except Exception:
                return None
        
        # Helper function for keyframing using Blender's standard API
        def insert_keyframe(obj, data_path, frame):
            """Insert keyframe using Blender's standard API (handles linked duplicates properly)"""
            if obj is None:
                print(f"Auto7Seg DEBUG: insert_keyframe called with None object!")
                return
            
            print(f"Auto7Seg DEBUG: insert_keyframe called for {obj.name}, data_path={data_path}, frame={frame}")
            
            # Ensure animation data exists (should already be set up, but check anyway)
            if not obj.animation_data:
                print(f"Auto7Seg DEBUG: Creating animation_data for {obj.name}")
                obj.animation_data_create()
            
            # Safety check: ensure action is unique (should already be done upfront, but double-check)
            if obj.animation_data.action:
                action_name = obj.animation_data.action.name
                users = obj.animation_data.action.users
                print(f"Auto7Seg DEBUG: {obj.name} has action '{action_name}' with {users} users")
                if users > 1:
                    print(f"Auto7Seg DEBUG: Action '{action_name}' is shared! Creating copy for {obj.name}")
                    obj.animation_data.action = obj.animation_data.action.copy()
                    print(f"Auto7Seg DEBUG: New action '{obj.animation_data.action.name}' created for {obj.name}")
            else:
                print(f"Auto7Seg DEBUG: {obj.name} has no action! This should not happen.")
            
            # Get current value before keyframing
            if data_path == 'rotation_euler':
                current_value = tuple(obj.rotation_euler)
            elif data_path == 'location':
                current_value = tuple(obj.location)
            elif data_path == 'scale':
                current_value = tuple(obj.scale)
            else:
                current_value = "unknown"
            
            print(f"Auto7Seg DEBUG: {obj.name} current {data_path} value: {current_value}")
            
            # Use Blender's standard keyframe_insert which handles everything properly
            # The frame parameter allows inserting at any frame without changing the current frame
            try:
                obj.keyframe_insert(data_path=data_path, frame=int(frame))
                print(f"Auto7Seg DEBUG: Successfully called keyframe_insert for {obj.name} at frame {frame}")
                
                # Verify keyframe was actually created (optional check, don't fail if this errors)
                try:
                    if obj.animation_data and obj.animation_data.action:
                        # Try to access fcurves - may not be available immediately or API may differ
                        if hasattr(obj.animation_data.action, 'fcurves'):
                            fcurves = obj.animation_data.action.fcurves
                            matching_fcurves = [fc for fc in fcurves if fc.data_path == data_path]
                            print(f"Auto7Seg DEBUG: {obj.name} has {len(matching_fcurves)} fcurves matching {data_path}")
                            for fc in matching_fcurves:
                                keyframe_count = len(fc.keyframe_points)
                                print(f"Auto7Seg DEBUG:   FCurve[{fc.array_index}] has {keyframe_count} keyframes")
                                if keyframe_count > 0:
                                    last_kf = fc.keyframe_points[-1]
                                    print(f"Auto7Seg DEBUG:     Last keyframe at frame {last_kf.co[0]}, value {last_kf.co[1]}")
                        else:
                            print(f"Auto7Seg DEBUG: Action '{obj.animation_data.action.name}' exists but fcurves not accessible (may be normal)")
                    else:
                        print(f"Auto7Seg DEBUG: WARNING - {obj.name} has no animation_data or action after keyframe_insert!")
                except Exception as verify_error:
                    # Don't fail on verification errors - keyframe_insert succeeded
                    print(f"Auto7Seg DEBUG: Could not verify keyframe (non-critical): {verify_error}")
            except Exception as e:
                print(f"Auto7Seg DEBUG: ERROR inserting keyframe for {obj.name}: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        # Ensure each segment has its own unique action before we start keyframing
        # This is critical for linked duplicates which may share actions
        print(f"Auto7Seg DEBUG: Initializing actions for {len(segments)} segments")
        for seg_idx, segment in enumerate(segments):
            if segment is None:
                print(f"Auto7Seg DEBUG: Segment {seg_idx} is None, skipping")
                continue
            
            print(f"Auto7Seg DEBUG: Processing segment {seg_idx}: {segment.name}")
            print(f"Auto7Seg DEBUG:   Type: {type(segment)}")
            print(f"Auto7Seg DEBUG:   Data: {segment.data.name if segment.data else 'None'}")
            
            if not segment.animation_data:
                print(f"Auto7Seg DEBUG:   Creating animation_data for {segment.name}")
                segment.animation_data_create()
            else:
                print(f"Auto7Seg DEBUG:   {segment.name} already has animation_data")
            
            if segment.animation_data.action:
                action_name = segment.animation_data.action.name
                users = segment.animation_data.action.users
                print(f"Auto7Seg DEBUG:   {segment.name} has action '{action_name}' with {users} users")
                # If action is shared, create a unique copy
                if users > 1:
                    old_action = segment.animation_data.action
                    segment.animation_data.action = old_action.copy()
                    print(f"Auto7Seg DEBUG:   Created unique action '{segment.animation_data.action.name}' for {segment.name} (was shared)")
                else:
                    print(f"Auto7Seg DEBUG:   {segment.name} action '{action_name}' is already unique")
            else:
                # Create new action if none exists
                new_action = bpy.data.actions.new(name=f"Auto7Seg_{segment.name}")
                segment.animation_data.action = new_action
                print(f"Auto7Seg DEBUG:   Created new action '{new_action.name}' for {segment.name}")
            
            # Final verification
            if segment.animation_data.action:
                final_users = segment.animation_data.action.users
                print(f"Auto7Seg DEBUG:   Final state: {segment.name} has action '{segment.animation_data.action.name}' with {final_users} users")
            else:
                print(f"Auto7Seg DEBUG:   ERROR: {segment.name} has no action after initialization!")
        
        # First, set all segments to their initial state (first digit) without keyframing
        # Keyframes will be added at the transition start instead
        first_digit = digits[0]
        first_pattern = DIGIT_PATTERNS[first_digit]
        
        print(f"Auto7Seg: Initializing state for digit {first_digit} (no keyframe yet)")
        
        for seg_idx, (segment, is_on) in enumerate(zip(segments, first_pattern)):
            if segment is None:
                print(f"Auto7Seg: Segment {seg_idx} is None, skipping")
                continue
            
            print(f"Auto7Seg: Processing segment {segment.name} (Idx: {seg_idx}), State: {'ON' if is_on else 'OFF'}")
            
            try:
                print(f"Auto7Seg DEBUG: Setting initial state for {segment.name}")
                
                if mode in ('LOCAL_ROTATION', 'GLOBAL_ROTATION'):
                    target_tuple = on_values_tuple if is_on else off_values_tuple
                    print(f"Auto7Seg DEBUG:   Applying rotation {target_tuple} to {segment.name}")
                    apply_rotation(segment, target_tuple, mode)
                else:
                    target_values = on_values if is_on else off_values
                    print(f"Auto7Seg DEBUG:   Applying {mode} {target_values} to {segment.name}")
                    if mode == 'GLOBAL_LOCATION':
                        if segment.parent:
                            parent_inv = segment.parent.matrix_world.inverted()
                            local_pos = parent_inv @ target_values
                        else:
                            local_pos = target_values
                        segment.location = local_pos
                    else:
                        apply_transform(segment, target_values, mode)
            except Exception as e:
                print(f"Auto7Seg ERROR processing segment {segment.name}: {e}")
                import traceback
                traceback.print_exc()
        
        # Now animate through all digits
        for digit_idx, digit in enumerate(digits):
            pattern = DIGIT_PATTERNS[digit]
            
            # For first digit, add two keyframes at the start with correct gap
            if digit_idx == 0:
                # Add two keyframes: one at current_frame, one at current_frame + (speed_frames - switch_frames)
                # The hold duration is speed_frames - switch_frames, then transition takes switch_frames
                first_keyframe = current_frame
                hold_end_keyframe = current_frame + (speed_frames - switch_frames)
                
                print(f"Auto7Seg DEBUG: Adding two keyframes for first digit {digit} at frames {first_keyframe} and {hold_end_keyframe} (hold duration: {speed_frames - switch_frames})")
                
                for seg_idx, (segment, is_on) in enumerate(zip(segments, first_pattern)):
                    if segment is None:
                        continue
                    
                    # First keyframe: current state (first digit)
                    if mode in ('LOCAL_ROTATION', 'GLOBAL_ROTATION'):
                        insert_keyframe(segment, 'rotation_euler', first_keyframe)
                    else:
                        insert_keyframe(segment, data_path, first_keyframe)
                    
                    # Second keyframe: same state (end of hold, start of transition)
                    if mode in ('LOCAL_ROTATION', 'GLOBAL_ROTATION'):
                        insert_keyframe(segment, 'rotation_euler', hold_end_keyframe)
                    else:
                        insert_keyframe(segment, data_path, hold_end_keyframe)
                
                # Move to transition start timing
                current_frame = hold_end_keyframe
                continue
            
            # Keyframe the previous state at start of transition (current position)
            # Skip adding keyframe at transition_start if it's the same frame as the previous digit's end
            transition_start = current_frame
            transition_end = current_frame + switch_frames
            
            # For digit 1, we need special handling since transition_start overlaps with digit 0's hold end
            if digit_idx == 1:
                # transition_start is already keyframed by digit 0's second keyframe (end of hold)
                # transition_end is the end of transition (start of digit 1's hold)
                # Only add keyframes for segments that change state
                print(f"Auto7Seg DEBUG: Processing digit {digit} transition from frame {transition_start} to {transition_end}")
                
                for seg_idx, (segment, is_on) in enumerate(zip(segments, pattern)):
                    if segment is None:
                        continue
                    
                    # Check if this segment changes state from digit 0 to digit 1
                    first_is_on = first_pattern[seg_idx]
                    state_changes = (first_is_on != is_on)
                    
                    if state_changes:
                        # Add keyframe at transition end for segments that change state
                        if mode in ('LOCAL_ROTATION', 'GLOBAL_ROTATION'):
                            target_tuple = on_values_tuple if is_on else off_values_tuple
                            apply_rotation(segment, target_tuple, mode)
                            insert_keyframe(segment, 'rotation_euler', transition_end)
                        else:
                            target_values = on_values if is_on else off_values
                            if mode == 'GLOBAL_LOCATION':
                                if segment.parent:
                                    parent_inv = segment.parent.matrix_world.inverted()
                                    local_pos = parent_inv @ target_values
                                else:
                                    local_pos = target_values
                                segment.location = local_pos
                            else:
                                apply_transform(segment, target_values, mode)
                            
                            insert_keyframe(segment, data_path, transition_end)
                    else:
                        # For segments that don't change, add keyframe at transition_end to maintain timing
                        # This ensures the hold continues correctly
                        if mode in ('LOCAL_ROTATION', 'GLOBAL_ROTATION'):
                            insert_keyframe(segment, 'rotation_euler', transition_end)
                        else:
                            insert_keyframe(segment, data_path, transition_end)
                
                # Move to next digit timing - transition_end + hold duration
                current_frame = transition_end + (speed_frames - switch_frames)
            else:
                # Normal processing for other digits
                print(f"Auto7Seg DEBUG: Processing digit {digit} at frames {transition_start}-{transition_end}")
                for seg_idx, (segment, is_on) in enumerate(zip(segments, pattern)):
                    if segment is None:
                        print(f"Auto7Seg DEBUG: Segment {seg_idx} is None, skipping")
                        continue
                    
                    print(f"Auto7Seg DEBUG: Processing segment {segment.name} for digit {digit}, state={'ON' if is_on else 'OFF'}")
                    
                    # Keyframe current state at transition start
                    print(f"Auto7Seg DEBUG: Keyframing {segment.name} at transition_start frame {transition_start}")
                    if mode in ('LOCAL_ROTATION', 'GLOBAL_ROTATION'):
                        insert_keyframe(segment, 'rotation_euler', transition_start)
                    else:
                        insert_keyframe(segment, data_path, transition_start)
                    
                    # Set target state and keyframe at transition end
                    if mode in ('LOCAL_ROTATION', 'GLOBAL_ROTATION'):
                        target_tuple = on_values_tuple if is_on else off_values_tuple
                        print(f"Auto7Seg DEBUG: Setting {segment.name} to rotation {target_tuple}")
                        apply_rotation(segment, target_tuple, mode)
                        insert_keyframe(segment, 'rotation_euler', transition_end)
                    else:
                        target_values = on_values if is_on else off_values
                        print(f"Auto7Seg DEBUG: Setting {segment.name} to {mode} {target_values}")
                        if mode == 'GLOBAL_LOCATION':
                            if segment.parent:
                                parent_inv = segment.parent.matrix_world.inverted()
                                local_pos = parent_inv @ target_values
                            else:
                                local_pos = target_values
                            segment.location = local_pos
                        else:
                            apply_transform(segment, target_values, mode)
                        
                        insert_keyframe(segment, data_path, transition_end)
                
                # Move to next digit timing
                current_frame += speed_frames
        
        # Determine if cyclic should be applied
        # For COUNT_UP and COUNT_DOWN, always add cyclic
        # For COUNT_FROM_TO, only add if cyclic checkbox is enabled
        should_add_cyclic = False
        if props.count_mode in ('COUNT_UP', 'COUNT_DOWN'):
            should_add_cyclic = True
        elif props.count_mode == 'COUNT_FROM_TO' and props.cyclic:
            should_add_cyclic = True
        
        # If cyclic, add transition from last digit back to first digit
        if should_add_cyclic and len(digits) > 0:
            print(f"Auto7Seg DEBUG: Adding transition from last digit back to first for cyclic animation")
            
            # Get the first and last digit patterns for looping
            first_digit = digits[0]
            first_pattern = DIGIT_PATTERNS[first_digit]
            last_digit = digits[-1]
            last_pattern = DIGIT_PATTERNS[last_digit]
            
            # Keyframe transition from last digit back to first digit
            transition_start = current_frame
            transition_end = current_frame + switch_frames
            
            print(f"Auto7Seg DEBUG: Transitioning from digit {last_digit} to {first_digit} at frames {transition_start}-{transition_end}")
            
            # Transition from last digit to first digit
            for seg_idx, (segment, last_is_on, first_is_on) in enumerate(zip(segments, last_pattern, first_pattern)):
                if segment is None:
                    continue
                
                print(f"Auto7Seg DEBUG: Processing cyclic transition segment {segment.name}, from {'ON' if last_is_on else 'OFF'} to {'ON' if first_is_on else 'OFF'}")
                
                # Keyframe current state (last digit) at transition start
                if mode in ('LOCAL_ROTATION', 'GLOBAL_ROTATION'):
                    insert_keyframe(segment, 'rotation_euler', transition_start)
                else:
                    insert_keyframe(segment, data_path, transition_start)
                
                # Set target state (first digit) and keyframe at transition end
                if mode in ('LOCAL_ROTATION', 'GLOBAL_ROTATION'):
                    target_tuple = on_values_tuple if first_is_on else off_values_tuple
                    print(f"Auto7Seg DEBUG: Setting {segment.name} to rotation {target_tuple} for cyclic transition")
                    apply_rotation(segment, target_tuple, mode)
                    insert_keyframe(segment, 'rotation_euler', transition_end)
                else:
                    target_values = on_values if first_is_on else off_values
                    print(f"Auto7Seg DEBUG: Setting {segment.name} to {mode} {target_values} for cyclic transition")
                    if mode == 'GLOBAL_LOCATION':
                        if segment.parent:
                            parent_inv = segment.parent.matrix_world.inverted()
                            local_pos = parent_inv @ target_values
                        else:
                            local_pos = target_values
                        segment.location = local_pos
                    else:
                        apply_transform(segment, target_values, mode)
                    
                    insert_keyframe(segment, data_path, transition_end)
            
            # Add one final keyframe that matches the first frame exactly for seamless looping
            # This ensures the Cycles modifier can loop seamlessly
            # Only add one keyframe at the end (transition_end already has the first digit state)
            final_frame = transition_end
            print(f"Auto7Seg DEBUG: Final keyframe already set at transition_end {final_frame} for seamless loop")
        
        # Verify first and last keyframes match for seamless looping (if cyclic)
        if should_add_cyclic and len(digits) > 0:
            print(f"Auto7Seg DEBUG: Verifying first and last keyframes match for seamless looping")
            
            # Determine the data path based on mode
            if mode in ('LOCAL_ROTATION', 'GLOBAL_ROTATION'):
                verify_data_path = 'rotation_euler'
            else:
                verify_data_path = data_path
            
            for segment in segments:
                if segment is None:
                    continue
                
                channelbag = get_channelbag(segment)
                if channelbag is None:
                    continue
                
                try:
                    for array_index in [0, 1, 2]:
                        fcurve = channelbag.fcurves.find(verify_data_path, index=array_index)
                        if fcurve is None:
                            continue
                        
                        # Get first and last keyframe values
                        if len(fcurve.keyframe_points) >= 2:
                            first_kf = fcurve.keyframe_points[0]
                            last_kf = fcurve.keyframe_points[-1]
                            
                            first_value = first_kf.co[1]
                            last_value = last_kf.co[1]
                            
                            # Check if values match (with small tolerance for floating point)
                            if abs(first_value - last_value) < 0.0001:
                                print(f"Auto7Seg DEBUG: {segment.name} FCurve[{array_index}] first ({first_value}) and last ({last_value}) values match")
                            else:
                                print(f"Auto7Seg DEBUG: WARNING - {segment.name} FCurve[{array_index}] first ({first_value}) and last ({last_value}) values don't match!")
                except Exception as e:
                    print(f"Auto7Seg DEBUG: Error verifying keyframes for {segment.name}: {e}")
        
        # Add Cycles F-modifier to all fcurves for cyclic animation
        if should_add_cyclic:
            # Determine the data path based on mode
            if mode in ('LOCAL_ROTATION', 'GLOBAL_ROTATION'):
                cyclic_data_path = 'rotation_euler'
            else:
                cyclic_data_path = data_path
            
            # Add Cycles modifier to all fcurves for each segment
            for segment in segments:
                if segment is None:
                    continue
                
                channelbag = get_channelbag(segment)
                if channelbag is None:
                    continue
                
                # Iterate through all array indices (0, 1, 2) for rotation_euler/location/scale
                for array_index in [0, 1, 2]:
                    fcurve = channelbag.fcurves.find(cyclic_data_path, index=array_index)
                    
                    if fcurve is None:
                        continue
                    
                    # Check if Cycles modifier already exists
                    has_cycles = any(mod.type == 'CYCLES' for mod in fcurve.modifiers)
                    
                    if not has_cycles:
                        try:
                            cycles_mod = fcurve.modifiers.new(type='CYCLES')
                            cycles_mod.mode_before = 'NONE'
                            cycles_mod.mode_after = 'REPEAT_OFFSET'
                            fcurve.update()
                        except Exception:
                            pass
        
        self.report({'INFO'}, f"Generated animation for {len(digits)} digits" + (" (cyclic)" if should_add_cyclic else ""))
        return {'FINISHED'}


class AUTO7SEG_PT_main_panel(Panel):
    """Main Auto7Seg panel in the N-panel"""
    bl_label = "Auto7Seg"
    bl_idname = "AUTO7SEG_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Auto7Seg'
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.auto7seg
        
        # Segment selection section
        box = layout.box()
        box.label(text="Segments", icon='MESH_DATA')
        
        col = box.column(align=True)
        col.prop(props, "segment_a", text="A (Top)")
        col.prop(props, "segment_b", text="B (Top-Right)")
        col.prop(props, "segment_c", text="C (Bottom-Right)")
        col.prop(props, "segment_d", text="D (Bottom)")
        col.prop(props, "segment_e", text="E (Bottom-Left)")
        col.prop(props, "segment_f", text="F (Top-Left)")
        col.prop(props, "segment_g", text="G (Middle)")
        
        # Only show rest if all segments assigned
        if not props.all_segments_assigned():
            box.label(text="Assign all 7 segments to continue", icon='INFO')
            return
        
        layout.separator()
        
        # Transform mode selection
        box = layout.box()
        box.label(text="Transform Mode", icon='ORIENTATION_GIMBAL')
        box.prop(props, "transform_mode", text="")
        
        layout.separator()
        
        # On/Off state values based on selected mode
        box = layout.box()
        box.label(text="On/Off States", icon='KEYFRAME')
        
        mode = props.transform_mode
        
        if mode == 'LOCAL_ROTATION':
            self.draw_transform_row(box, props, "on_local_rotation", "On Rotation")
            self.draw_transform_row(box, props, "off_local_rotation", "Off Rotation")
        elif mode == 'GLOBAL_ROTATION':
            self.draw_transform_row(box, props, "on_global_rotation", "On Rotation")
            self.draw_transform_row(box, props, "off_global_rotation", "Off Rotation")
        elif mode == 'LOCAL_LOCATION':
            self.draw_transform_row(box, props, "on_local_location", "On Location")
            self.draw_transform_row(box, props, "off_local_location", "Off Location")
        elif mode == 'GLOBAL_LOCATION':
            self.draw_transform_row(box, props, "on_global_location", "On Location")
            self.draw_transform_row(box, props, "off_global_location", "Off Location")
        else:  # SCALE
            self.draw_transform_row(box, props, "on_scale", "On Scale")
            self.draw_transform_row(box, props, "off_scale", "Off Scale")
        
        layout.separator()
        
        # Timing settings
        box = layout.box()
        box.label(text="Timing", icon='TIME')
        
        row = box.row()
        row.prop(props, "time_unit", expand=True)
        
        unit_label = "frames" if props.time_unit == 'FRAMES' else "seconds"
        box.prop(props, "speed", text=f"Speed ({unit_label})")
        box.prop(props, "switching_speed", text=f"Switch Speed ({unit_label})")
        
        layout.separator()
        
        # Count mode settings
        box = layout.box()
        box.label(text="Count Mode", icon='LINENUMBERS_ON')
        box.prop(props, "count_mode", text="")
        
        if props.count_mode == 'COUNT_FROM_TO':
            row = box.row(align=True)
            row.prop(props, "count_from", text="From")
            row.prop(props, "count_to", text="To")
        
        # Cyclic checkbox (always visible)
        box.prop(props, "cyclic", text="Cyclic (Loop to First Digit)")
        
        layout.separator()
        
        # Generate button
        layout.operator("auto7seg.generate_animation", text="Generate Animation", icon='RENDER_ANIMATION')
    
    def draw_transform_row(self, layout, props, prop_name, label):
        """Draw a transform property with set-to-active buttons for each axis"""
        col = layout.column(align=True)
        col.label(text=label)
        
        axis_labels = ['X', 'Y', 'Z']
        
        for i, axis in enumerate(axis_labels):
            row = col.row(align=True)
            row.prop(props, prop_name, index=i, text=axis)
            
            op = row.operator("auto7seg.set_to_active", text="", icon='EYEDROPPER')
            op.property_name = prop_name
            op.axis = i


# Registration
classes = (
    Auto7SegProperties,
    AUTO7SEG_OT_set_to_active,
    AUTO7SEG_OT_generate_animation,
    AUTO7SEG_PT_main_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.auto7seg = PointerProperty(type=Auto7SegProperties)


def unregister():
    del bpy.types.Scene.auto7seg
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
