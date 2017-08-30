"""
NOTICE
 
This software was produced for the U. S. Government
under Basic Contract No. W15P7T-13-C-A802, and is
subject to the Rights in Noncommercial Computer Software
and Noncommercial Computer Software Documentation
Clause 252.227-7014 (FEB 2012)
 
(C) 2017 The MITRE Corporation

"""

import imp
import os
import logging

logger = logging.getLogger('app.plugins')


class PluginLoader:
    def __init__(self, plugin_path='plugins'):
        self.plugin_path = plugin_path
        self.plugins = {}

    def enumerate_plugins(self):
        # Get list of plugins
        if os.path.isdir(self.plugin_path):
            for top_dir_name in os.listdir(self.plugin_path):
                top_path = os.path.join(self.plugin_path, top_dir_name)
                if os.path.isdir(top_path):
                    for sub_file in os.listdir(top_path):
                        if sub_file.endswith('_main.py'):
                            # self.plugins[sub_file.rstrip('_main.py')] = os.path.join(top_path, sub_file)
                            self.plugins[sub_file.rstrip('_main.py')] = imp.find_module(sub_file.rstrip('.py'), [top_path])
        else:
            logger.warning("Couldn't find plugin directory at ./{} (will not load plugins)".format(self.plugin_path))

    def load_plugins(self):
        for plugin_name, plugin_found_module in self.plugins.items():
            logger.info("[PLUGINS] Loading {}".format(plugin_name))
            try:
                imp.load_module(plugin_name, *plugin_found_module)
            except ImportError as e:
                logger.warning("[PLUGINS] Loading {} failed with {}".format(plugin_name, e))
            finally:
                plugin_found_module[0].close()  # Close the module file.
