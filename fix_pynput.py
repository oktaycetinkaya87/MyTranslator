import sys
import logging

# Monkey Patch for pynput crash on macOS (KeyError: 'AXIsProcessTrusted')
# This happens when pyobjc's HIServices bridge is incomplete or fails to load the symbol.

try:
    import HIServices
    
    # Try to access the function to see if it exists
    # If it raises KeyError (from objc._lazyimport), we need to patch it.
    try:
        _ = HIServices.AXIsProcessTrusted
    except (KeyError, AttributeError):
        logging.warning("🔧 Patching missing HIServices.AXIsProcessTrusted...")
        
        # Define a dummy function that returns True (Trusted)
        # This bypasses the check in pynput
        def AXIsProcessTrusted():
            return True
            
        # Inject it into the module
        # setattro ensures we overwrite it even if it's a lazy object
        setattr(HIServices, 'AXIsProcessTrusted', AXIsProcessTrusted)
        
except ImportError:
    # If HIServices is totally missing, mock the whole module
    logging.warning("🔧 HIServices not found. Mocking module for pynput.")
    from unittest.mock import MagicMock
    m = MagicMock()
    m.AXIsProcessTrusted.return_value = True
    sys.modules['HIServices'] = m
    
except Exception as e:
    logging.error(f"❌ Error applying Pynput Fix: {e}")
