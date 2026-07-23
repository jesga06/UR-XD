import unittest
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

from src.mapper import Mapper
from src.decoder import ControllerState
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

    def test_reverse_order_rejects_chord(self):
        mapper = Mapper(self.cfg)
        st = ControllerState()
        
        # RB pressed first
        st.rb = 1.0
        mapper.process(st)
        self.assertEqual(mapper.active_layer, 'layer_base')
        
        time.sleep(0.01)
        # LB pressed second -> t_lb > t_rb, chord shift_2 rejected, single shift_1 activated
        st.lb = 1.0
        mapper.process(st)
        self.assertEqual(mapper.active_layer, 'shift_1')

if __name__ == '__main__':
    unittest.main()
