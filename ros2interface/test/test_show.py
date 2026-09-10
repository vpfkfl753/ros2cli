# Copyright 2026 vpfkfl753
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest

from ros2interface.verb.show import _get_interface_lines


@pytest.mark.parametrize('interface_kind', ['msg', 'srv', 'action'])
@pytest.mark.parametrize('subdirectory', ['', 'nested/'])
@pytest.mark.parametrize('include_exact_name', [False, True])
def test_get_interface_lines_matches_full_name(
    tmp_path, monkeypatch, interface_kind, subdirectory, include_exact_name
):
    package_name = 'test_interfaces'
    resource_index = tmp_path / 'share' / 'ament_index' / 'resource_index'
    for resource_type in ('packages', 'rosidl_interfaces'):
        (resource_index / resource_type).mkdir(parents=True)
    (resource_index / 'packages' / package_name).write_text('')

    share_dir = tmp_path / 'share' / package_name
    interfaces = [('OtherFoo', 'bool wrong')]
    if include_exact_name:
        interfaces.append(('Foo', 'int32 value'))
    separators = {'msg': 0, 'srv': 1, 'action': 2}[interface_kind]
    paths = []
    for name, definition in interfaces:
        relative_path = f'{subdirectory}{interface_kind}/{name}.{interface_kind}'
        path = share_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(definition + '\n' + '---\n' * separators)
        paths.append(relative_path)
    (resource_index / 'rosidl_interfaces' / package_name).write_text('\n'.join(paths))
    monkeypatch.setenv('AMENT_PREFIX_PATH', str(tmp_path))

    identifier = f'{package_name}/{interface_kind}/Foo'
    if include_exact_name:
        expected = ['int32 value'] + ['---'] * separators
        assert [str(line) for line in _get_interface_lines(identifier)] == expected
    else:
        with pytest.raises(LookupError, match='not found in package'):
            list(_get_interface_lines(identifier))


@pytest.mark.parametrize('interface_kind', ['msg', 'srv', 'action'])
@pytest.mark.parametrize('canonical_index', [0, 1, 2])
def test_get_interface_lines_prefers_canonical_path(
    tmp_path, monkeypatch, interface_kind, canonical_index
):
    package_name = 'test_interfaces'
    resource_index = tmp_path / 'share' / 'ament_index' / 'resource_index'
    for resource_type in ('packages', 'rosidl_interfaces'):
        (resource_index / resource_type).mkdir(parents=True)
    (resource_index / 'packages' / package_name).write_text('')

    canonical_path = f'{interface_kind}/Foo.{interface_kind}'
    paths = [f'nested/{canonical_path}', f'other/{canonical_path}']
    paths.insert(canonical_index, canonical_path)
    separators = {'msg': 0, 'srv': 1, 'action': 2}[interface_kind]
    for relative_path in paths:
        path = tmp_path / 'share' / package_name / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        definition = 'int32 value' if relative_path == canonical_path else 'bool wrong'
        path.write_text(definition + '\n' + '---\n' * separators)
    (resource_index / 'rosidl_interfaces' / package_name).write_text('\n'.join(paths))
    monkeypatch.setenv('AMENT_PREFIX_PATH', str(tmp_path))

    expected = ['int32 value'] + ['---'] * separators
    identifier = f'{package_name}/{interface_kind}/Foo'
    assert [str(line) for line in _get_interface_lines(identifier)] == expected
