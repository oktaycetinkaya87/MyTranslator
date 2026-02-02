import logging
import sys

# Configure Logging (Do this at the very top of ui/popup_window.py if not already importing logging)
# But since I am patching the file, I should ensure logging is imported.
# It seems ui/popup_window.py didn't import logging in Step 302.
