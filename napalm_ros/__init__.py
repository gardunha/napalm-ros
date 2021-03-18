"""napalm_ros package."""

# Import stdlib
import pkg_resources

# Import local modules
from napalm_ros.ros import ROSDriver

try:
    __version__ = pkg_resources.get_distribution('napalm-ros').version
except pkg_resources.DistributionNotFound:
    __version__ = "Not installed"

__all__ = ('ROSDriver', )

# Define the Netbox plugin metadata if Netbox is installed
try:
    from extras.plugins import PluginConfig
except ImportError:
    pass
else:
    class NapalmRosConfig(PluginConfig):
        name = 'napalm_ros'
        verbose_name = 'NAPALM RouterOS'
        description = 'NAPALM Driver for RouterOS'
        version = '1.0.1'
        author = 'Łukasz Kostka'
        author_email = 'lukasz.kostka@netng.pl'
        base_url = 'napalm-ros'
        required_settings = []
        default_settings = {
        }

    config = NapalmRosConfig
