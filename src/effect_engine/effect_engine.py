import numpy as np
import sys
import os
from typing import Dict, List, Any, Optional, Type
from .base_effect import BaseEffect
from .the_flippy import TheFlippy
from .gradient_overlay_simple import GradientOverlaySimple
from .the_stutter import TheStutter
from .ki import Ki
from .miner import Miner
from .spotlight import Spotlight

class EffectEngine:
    """Engine for managing and applying visual effects."""
    
    def __init__(self):
        self.effects = {}  # name -> effect instance
        self.effect_chain = []  # ordered list of effect names to apply
        self.global_parameters = {
            'intensity': 1.0,
            'mix': 1.0,
            'frame_rate': 30.0
        }
        
        # Directly register all available effects
        self.effect_classes = {
            'TheFlippy': TheFlippy,
            'GradientOverlaySimple': GradientOverlaySimple,
            'TheStutter': TheStutter,
            'Ki': Ki,
            'Miner': Miner,
            'Spotlight': Spotlight
        }
        
    def register_effect_class(self, effect_class: Type[BaseEffect], name: Optional[str] = None):
        """
        Register an effect class.
        
        Args:
            effect_class: Class that inherits from BaseEffect
            name: Optional name override
        """
        if not issubclass(effect_class, BaseEffect):
            raise ValueError("Effect class must inherit from BaseEffect")
            
        effect_name = name or effect_class.__name__
        self.effect_classes[effect_name] = effect_class
        
    def discover_effects(self, effects_directory: str):
        """
        Discover and register effects from a directory.
        
        Args:
            effects_directory: Path to directory containing effect modules
        """
        if not os.path.exists(effects_directory):
            print(f"Effects directory not found: {effects_directory}")
            return
            
        for filename in os.listdir(effects_directory):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]
                try:
                    # Import the module
                    spec = importlib.util.spec_from_file_location(
                        module_name, 
                        os.path.join(effects_directory, filename)
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find effect classes in the module
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseEffect) and 
                            obj != BaseEffect):
                            self.register_effect_class(obj, name)
                            print(f"Registered effect: {name}")
                            
                except Exception as e:
                    print(f"Error loading effect module {module_name}: {e}")
                    
    def create_effect(self, effect_name: str, instance_name: Optional[str] = None) -> bool:
        """
        Create an instance of an effect.
        
        Args:
            effect_name: Name of registered effect class
            instance_name: Name for this instance (defaults to effect_name)
            
        Returns:
            True if effect was created successfully
        """
        if effect_name not in self.effect_classes:
            print(f"Effect class not found: {effect_name}")
            return False
            
        instance_name = instance_name or effect_name
        
        if instance_name in self.effects:
            print(f"Effect instance already exists: {instance_name}")
            return False
            
        try:
            effect_instance = self.effect_classes[effect_name](instance_name)
            self.effects[instance_name] = effect_instance
            return True
        except Exception as e:
            print(f"Error creating effect {effect_name}: {e}")
            return False
            
    def remove_effect(self, instance_name: str) -> bool:
        """
        Remove an effect instance.
        
        Args:
            instance_name: Name of effect instance to remove
            
        Returns:
            True if effect was removed successfully
        """
        if instance_name not in self.effects:
            return False
            
        # Remove from effect chain
        if instance_name in self.effect_chain:
            self.effect_chain.remove(instance_name)
            
        # Cleanup effect
        self.effects[instance_name].cleanup()
        del self.effects[instance_name]
        return True
        
    def add_to_chain(self, instance_name: str, position: Optional[int] = None):
        """
        Add effect to processing chain.
        
        Args:
            instance_name: Name of effect instance
            position: Position in chain (None = append to end)
        """
        if instance_name not in self.effects:
            print(f"Effect instance not found: {instance_name}")
            return
            
        if instance_name in self.effect_chain:
            self.effect_chain.remove(instance_name)
            
        if position is None:
            self.effect_chain.append(instance_name)
        else:
            self.effect_chain.insert(position, instance_name)
            
    def remove_from_chain(self, instance_name: str):
        """Remove effect from processing chain."""
        if instance_name in self.effect_chain:
            self.effect_chain.remove(instance_name)
            
    def reorder_chain(self, new_order: List[str]):
        """
        Reorder the effect chain.
        
        Args:
            new_order: List of effect instance names in desired order
        """
        # Validate all effects exist
        for name in new_order:
            if name not in self.effects:
                print(f"Effect not found: {name}")
                return
                
        self.effect_chain = new_order.copy()
        
    def process_frame(self, frame: np.ndarray, audio_data: Dict[str, Any]) -> np.ndarray:
        """
        Process frame through the effect chain.
        
        Args:
            frame: Input video frame
            audio_data: Audio analysis data
            
        Returns:
            Processed frame
        """
        if frame is None:
            return frame
            
        current_frame = frame.copy()
        
        # Apply global intensity
        intensity = self.global_parameters.get('intensity', 1.0)
        
        # Process through effect chain
        for effect_name in self.effect_chain:
            if effect_name not in self.effects:
                continue
                
            effect = self.effects[effect_name]
            if not effect.is_enabled():
                continue
                
            try:
                # Process frame
                processed_frame = effect.process_frame(current_frame, audio_data)
                
                # Apply global mix
                mix = self.global_parameters.get('mix', 1.0) * intensity
                if mix < 1.0:
                    current_frame = (
                        (1.0 - mix) * current_frame + 
                        mix * processed_frame
                    ).astype(current_frame.dtype)
                else:
                    current_frame = processed_frame
                    
            except Exception as e:
                print(f"Error processing effect {effect_name}: {e}")
                
        return current_frame
        
    def get_effect_list(self) -> List[str]:
        """Get list of available effect classes."""
        return list(self.effect_classes.keys())
        
    def get_instance_list(self) -> List[str]:
        """Get list of created effect instances."""
        return list(self.effects.keys())
        
    def get_effect_chain(self) -> List[str]:
        """Get current effect processing chain."""
        return self.effect_chain.copy()
        
    def get_effect_instance(self, instance_name: str) -> Optional[BaseEffect]:
        """Get effect instance by name."""
        return self.effects.get(instance_name)
        
    def set_global_parameter(self, name: str, value: Any):
        """Set global engine parameter."""
        self.global_parameters[name] = value
        
    def get_global_parameter(self, name: str, default: Any = None) -> Any:
        """Get global engine parameter."""
        return self.global_parameters.get(name, default)
        
    def get_global_parameters(self) -> Dict[str, Any]:
        """Get all global parameters."""
        return self.global_parameters.copy()
        
    def initialize_effects(self, frame_shape: tuple):
        """Initialize all effects with frame dimensions."""
        for effect in self.effects.values():
            try:
                effect.initialize(frame_shape)
            except Exception as e:
                print(f"Error initializing effect {effect.get_name()}: {e}")
                
    def reset_all_effects(self):
        """Reset all effects to initial state."""
        for effect in self.effects.values():
            try:
                effect.reset()
            except Exception as e:
                print(f"Error resetting effect {effect.get_name()}: {e}")
                
    def cleanup(self):
        """Cleanup all effects and resources."""
        for effect in self.effects.values():
            try:
                effect.cleanup()
            except Exception as e:
                print(f"Error cleaning up effect {effect.get_name()}: {e}")
                
        self.effects.clear()
        self.effect_chain.clear()