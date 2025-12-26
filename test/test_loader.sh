set -exu
echo "## _modules"
salt-call --local test_module.ping

echo
echo "## _states"
salt-call --local state.single test_state.present name=smoketest

echo
echo "## _grains"
salt-call --local grains.get test_grain

echo
echo "## _renderers"
salt-call --local sys.list_renderers | grep test_renderer

echo
echo "## _returners"
salt-call --local sys.list_returners | grep test_returner

echo
echo "## _output"
salt-call --local test_module.ping --out=test_output

echo
echo "## _beacons"
salt-call --local sys.list_beacons | grep test_beacon

echo
echo "## _utils"
salt-call --local sys.list_utils | grep test_utils

echo
echo "## _serializers"
salt-call --local sys.list_serializers | grep test_serializer

echo
echo "## _executors"
salt-call --local sys.list_executors | grep test_executor

echo
echo "## _wrappers"
salt-call --local sys.list_wrappers | grep test_wrapper

echo
echo "## _matchers"
salt-call --local sys.list_matchers | grep test_matcher