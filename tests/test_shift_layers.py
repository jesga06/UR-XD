import unittest
import sys
import os
import tempfile
import json
from src.config_manager import ControllerConfig

class TestShiftLayersConfig(unittest.TestCase):
    def test_default_shift_layers(self):
        cfg = ControllerConfig()
        layers = cfg.get_shift_layers()
        self.assertEqual(len(layers), 1)
        self.assertEqual(layers[0]['id'], 'shift_1')
        self.assertEqual(layers[0]['name'], 'Shift Layer 1')

    def test_legacy_migration(self):
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.json') as f:
            legacy_data = {
                "shift_layer": {
                    "mode": "toggle",
                    "trigger_button": "lb"
                },
                "shift_mappings": {"a": "keyboard:x"},
                "shift_block_xinput": {"a": "true"}
            }
            json.dump(legacy_data, f)
            temp_path = f.name

        try:
            cfg = ControllerConfig(temp_path)
            layers = cfg.get_shift_layers()
            self.assertEqual(len(layers), 1)
            self.assertEqual(layers[0]['trigger_button'], 'lb')
            self.assertEqual(layers[0]['mode'], 'toggle')
            self.assertEqual(layers[0]['mappings'].get('a'), 'keyboard:x')
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_add_and_remove_shift_layer(self):
        cfg = ControllerConfig()
        layer2 = cfg.add_shift_layer(name="Sniper Layer", trigger_button="lb", modifier_button="rb", mode="hold")
        layers = cfg.get_shift_layers()
        self.assertEqual(len(layers), 2)
        self.assertEqual(layers[1]['id'], 'shift_2')
        self.assertEqual(layers[1]['name'], 'Sniper Layer')
        self.assertEqual(layers[1]['trigger_button'], 'lb')
        self.assertEqual(layers[1]['modifier_button'], 'rb')

        cfg.remove_shift_layer('shift_2')
        layers_after = cfg.get_shift_layers()
        self.assertEqual(len(layers_after), 1)

    def test_duplicate_layer_id_deduplication(self):
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.json') as f:
            duplicate_id_data = {
                "shift_layers": [
                    {
                        "id": "shift_2",
                        "name": "First Shift 2",
                        "trigger_button": "home",
                        "modifier_button": "",
                        "mode": "hold",
                        "mappings": {"a": "keyboard:x"}
                    },
                    {
                        "id": "shift_2",
                        "name": "Second Shift 2",
                        "trigger_button": "home",
                        "modifier_button": "rb",
                        "mode": "hold",
                        "mappings": {"b": "keyboard:y"}
                    }
                ]
            }
            json.dump(duplicate_id_data, f)
            temp_path = f.name

        try:
            cfg = ControllerConfig(temp_path)
            layers = cfg.get_shift_layers()
            self.assertEqual(len(layers), 2)
            self.assertEqual(layers[0]['id'], 'shift_1')
            self.assertEqual(layers[1]['id'], 'shift_2')

            # Add layer after deletion scenario
            new_layer = cfg.add_shift_layer(name="New Layer")
            self.assertEqual(new_layer['id'], 'shift_3')
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

from unittest.mock import patch, MagicMock

if 'hid' not in sys.modules:
    try:
        import hid
    except (ImportError, Exception):
        sys.modules['hid'] = MagicMock()

from src.mapper import Mapper
from src.decoder import ControllerState
from src.virtual_pad import VirtualPad
import time

class TestMapperShiftLayers(unittest.TestCase):
    def setUp(self):
        self.cfg = ControllerConfig()
        self.cfg.set_shift_layers([
            {
                "id": "shift_1",
                "name": "Single Shift",
                "trigger_button": "lb",
                "modifier_button": "",
                "mode": "hold",
                "mappings": {"a": "keyboard:1"},
                "block_xinput": {}
            },
            {
                "id": "shift_2",
                "name": "Chord Shift",
                "trigger_button": "lb",
                "modifier_button": "rb",
                "mode": "hold",
                "mappings": {"a": "keyboard:2"},
                "block_xinput": {}
            }
        ])

    def test_single_shift_activation(self):
        mapper = Mapper(self.cfg)
        st = ControllerState()
        st.lb = 1.0
        mapper.process(st)
        self.assertEqual(mapper.active_layer, 'shift_1')

    def test_strict_order_chord_activation(self):
        mapper = Mapper(self.cfg)
        st = ControllerState()
        
        # LB pressed first
        st.lb = 1.0
        mapper.process(st)
        self.assertEqual(mapper.active_layer, 'shift_1')
        
        time.sleep(0.01)
        # RB pressed second -> chord activates shift_2
        st.rb = 1.0
        mapper.process(st)
        self.assertEqual(mapper.active_layer, 'shift_2')

    def test_toggle_mode_activation(self):
        cfg = ControllerConfig()
        cfg.set_shift_layers([
            {
                "id": "shift_toggle",
                "name": "Toggle Shift",
                "trigger_button": "lb",
                "modifier_button": "",
                "mode": "toggle",
                "mappings": {"a": "keyboard:t"},
                "block_xinput": {}
            }
        ])
        mapper = Mapper(cfg)
        st = ControllerState()
        
        # 1. Press LB -> toggles ON
        st.lb = 1.0
        mapper.process(st)
        self.assertEqual(mapper.active_layer, 'shift_toggle')
        
        # 2. Release LB -> stays ON
        st.lb = 0.0
        mapper.process(st)
        self.assertEqual(mapper.active_layer, 'shift_toggle')
        
        # 3. Press LB again -> toggles OFF
        st.lb = 1.0
        mapper.process(st)
        self.assertEqual(mapper.active_layer, 'layer_base')

    def test_modifier_none_string_normalization(self):
        cfg = ControllerConfig()
        cfg.set_shift_layers([
            {
                "id": "shift_1",
                "name": "Base Shift",
                "trigger_button": "home",
                "modifier_button": "none",
                "mode": "hold",
                "mappings": {"a": "keyboard:1"},
                "block_xinput": {}
            },
            {
                "id": "shift_2",
                "name": "Base2 Shift",
                "trigger_button": "home",
                "modifier_button": "rb",
                "mode": "hold",
                "mappings": {"a": "keyboard:2"},
                "block_xinput": {}
            }
        ])
        mapper = Mapper(cfg)
        st = ControllerState()
        
        # Press HOME only -> must match shift_1 (single trigger layer after "none" string normalization)
        st.home = 1.0
        mapper.process(st)
        self.assertEqual(mapper.active_layer, 'shift_1')
        
        # Press RB too -> must match shift_2 (chord layer)
        st.rb = 1.0
        mapper.process(st)
        self.assertEqual(mapper.active_layer, 'shift_2')

    def test_dynamic_per_layer_xinput_blocking(self):
        cfg = ControllerConfig()
        cfg.set_shift_layers([
            {
                "id": "shift_1",
                "name": "Shift Layer 1",
                "trigger_button": "home",
                "modifier_button": "",
                "mode": "hold",
                "mappings": {"a": "keyboard:x"},
                "block_xinput": {"a": "true"}
            }
        ])
        vp = VirtualPad(cfg)
        mapper = Mapper(cfg)
        vp.mapper = mapper

        st = ControllerState()
        active_layer_id = getattr(vp.mapper, 'active_layer', 'layer_base')
        base_blocks = vp.layer_blocked_buttons.get(active_layer_id, set())
        self.assertNotIn('a', base_blocks)

        st.home = 1.0
        mapper.process(st)
        self.assertEqual(mapper.active_layer, 'shift_1')

        shift_blocks = vp.layer_blocked_buttons.get(mapper.active_layer, set())
        self.assertIn('a', shift_blocks)

    def test_unmapped_button_fallback_to_base(self):
        cfg = ControllerConfig()
        cfg.set_shift_layers([
            {
                "id": "shift_1",
                "name": "Shift Layer 1",
                "trigger_button": "home",
                "modifier_button": "",
                "mode": "hold",
                "mappings": {},
                "block_xinput": {}
            }
        ])
        cfg.data["layer_base"] = {"a": "keyboard:space"}
        mapper = Mapper(cfg)

        st = ControllerState()
        st.home = 1.0
        mapper.process(st)
        self.assertEqual(mapper.active_layer, 'shift_1')

        st.a = 1.0
        mapper.process(st)
        self.assertIn('a', mapper.active_holds)
        self.assertEqual(mapper.active_holds['a'], 'keyboard:space')

if __name__ == '__main__':
    unittest.main()
