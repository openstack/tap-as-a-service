# Copyright (C) 2016 Midokura SARL.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import abc


class TaasBaseDriver(metaclass=abc.ABCMeta):

    def __init__(self, service_plugin):
        self.service_plugin = service_plugin

    @property
    def service_type(self):
        pass

    @abc.abstractmethod
    def create_tap_service_precommit(self, context):
        pass

    @abc.abstractmethod
    def delete_tap_service_precommit(self, context):
        pass

    @abc.abstractmethod
    def create_tap_flow_precommit(self, context):
        pass

    @abc.abstractmethod
    def delete_tap_flow_precommit(self, context):
        pass

    @abc.abstractmethod
    def create_tap_service_postcommit(self, context):
        pass

    @abc.abstractmethod
    def delete_tap_service_postcommit(self, context):
        pass

    @abc.abstractmethod
    def create_tap_flow_postcommit(self, context):
        pass

    @abc.abstractmethod
    def delete_tap_flow_postcommit(self, context):
        pass

    @abc.abstractmethod
    def create_tap_mirror_precommit(self, context):
        pass

    @abc.abstractmethod
    def create_tap_mirror_postcommit(self, context):
        pass

    @abc.abstractmethod
    def delete_tap_mirror_precommit(self, context):
        pass

    @abc.abstractmethod
    def delete_tap_mirror_postcommit(self, context):
        pass
