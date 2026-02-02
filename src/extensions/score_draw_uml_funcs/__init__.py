# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""
This 'sphinx-extension' is responsible to allow for functional drawings of UML diagrams

    - Features
    - Logical Interfaces
    - Modules
    - Components
    - Component Interfaces

and all applicable linkages between them.

It provides this functionality by adding classes to `needs_render_context`,
which then can be invoked inside 'needarch' and 'needuml' blocks in rst files.
"""

import hashlib
import time
from collections.abc import Callable
from functools import cache
from pathlib import Path
from typing import Any, cast

from score_draw_uml_funcs.helpers import (
    gen_header,
    gen_interface_element,
    gen_link_text,
    gen_struct_element,
    get_alias,
    get_hierarchy_text,
    get_impl_comp_from_logic_iface,
    get_interface_from_component,
    get_interface_from_int,
    get_module,
)
from sphinx.application import Sphinx
from sphinx_needs.logging import get_logger

CollectResult = tuple[
    str,  # structure_text
    str,  # link_text
    dict[str, str],  # proc_impl_interfaces
    dict[str, list[str]],  # proc_used_interfaces
    dict[str, list[str]],  # impl_comp - Changed to list[str] to support multiple components per interface
    list[str],  # proc_modules
]

logger = get_logger(__file__)


def setup(app: Sphinx) -> dict[str, object]:
    app.config.needs_render_context = draw_uml_function_context
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


@cache
def scripts_directory_hash():
    start = time.time()
    all = ""
    for file in Path(".devcontainer/sphinx_conf").glob("**/*.py"):
        with open(file) as f:
            all += f.read()
    hash_object = hashlib.sha256(all.encode("utf-8"))
    directory_hash = hash_object.hexdigest()
    logger.info(
        "calculate directory_hash = "
        + directory_hash
        + " within "
        + str(time.time() - start)
        + " seconds."
    )
    return directory_hash


#       ╭──────────────────────────────────────────────────────────────────────────────╮
#       │                           Actual drawing functions                           │
#       ╰──────────────────────────────────────────────────────────────────────────────╯


def _process_interfaces(
    iface_list: list[str],
    relation: str,
    need: dict[str, str],
    all_needs: dict[str, dict[str, str]],
    proc_dict: dict[str, str] | dict[str, list[str]],
    linkage_text: str,
) -> str:
    """Helper to process either implemented or used interfaces."""

    for iface in iface_list:
        # check for misspelled interface
        if not all_needs.get(iface, []):
            logger.info(f"{need}: {relation} {iface} could not be found")
            continue

        if relation == "implements":
            # Changed to support multiple components implementing the same interface
            proc_impl_dict = cast(dict[str, list[str]], proc_dict)
            if not proc_impl_dict.get(iface, []):
                proc_impl_dict[iface] = []
            
            # Only add linkage if this component hasn't already been processed for this interface
            if need["id"] not in proc_impl_dict[iface]:
                linkage_text += (
                    f"{gen_link_text(need, '-u->', all_needs[iface], 'implements')} \n"
                )
                proc_impl_dict[iface].append(need["id"])
        else:  # "uses"
            proc_used_dict = cast(dict[str, list[str]], proc_dict)
            if not proc_used_dict.get(iface, []):
                proc_used_dict[iface] = [need["id"]]
            else:
                proc_used_dict[iface].append(need["id"])

    return linkage_text


def draw_comp_incl_impl_int(
    need: dict[str, str],
    all_needs: dict[str, dict[str, str]],
    proc_impl_interfaces: dict[str, list[str]],
    proc_used_interfaces: dict[str, list[str]],
    white_box_view: bool = False,
) -> tuple[str, str, dict[str, list[str]], dict[str, list[str]]]:
    """This function draws a component including any interfaces which are implemented
    by the component

    :param dict[str,str] need: Component which should be drawn
    :param dict all_needs: Dictionary containing all needs
    :param dict[str,dict] proc_impl_interfaces: Dictionary containing
    all implemented interfaces which were already processed during this cycle
    :param dict[str,dict] proc_used_interfaces: Dictionary containing
    all used interfaces which were already processed during this cycle
    """
    # Draw outer component
    structure_text = f"{gen_struct_element('component', need)}  {{\n"
    linkage_text = ""

    # Draw inner (sub)components recursively if requested
    if white_box_view:
        # Process both includes and consists_of for sub-components
        sub_components = need.get("includes", []) + need.get("consists_of", [])
        for need_inc in sub_components:
            curr_need = all_needs.get(need_inc, {})

            # check for misspelled include
            if not curr_need:
                logger.info(f"{need}: include {need_inc} could not be found")
                continue

            if curr_need["type"] not in ["comp", "comp_arc_sta"]:
                continue

            # Check if this sub-component is also a container
            sub_is_container = bool(curr_need.get("consists_of"))
            
            sub_structure, sub_linkage, proc_impl_interfaces, proc_used_interfaces = (
                draw_comp_incl_impl_int(
                    curr_need, all_needs, proc_impl_interfaces, proc_used_interfaces,
                    white_box_view=sub_is_container  # Only enable white-box view if sub-component is also a container
                )
            )

            structure_text += sub_structure
            linkage_text += sub_linkage

    # close outer component
    structure_text += f"}} /' {need['title']} '/ \n\n"

    # Find implemented real interfaces inside the module/component
    local_impl_interfaces = get_interface_from_component(need, "implements", all_needs)
    local_used_interfaces = get_interface_from_component(need, "uses", all_needs)

    # Process implemented interfaces
    linkage_text = _process_interfaces(
        local_impl_interfaces,
        "implements",
        need,
        all_needs,
        proc_impl_interfaces,
        linkage_text,
    )

    # Process used interfaces
    linkage_text = _process_interfaces(
        local_used_interfaces,
        "uses",
        need,
        all_needs,
        proc_used_interfaces,
        linkage_text,
    )

    return structure_text, linkage_text, proc_impl_interfaces, proc_used_interfaces


def draw_impl_interface(
    need: dict[str, str],
    all_needs: dict[str, dict[str, str]],
    local_impl_interfaces: set[str],
) -> set[str]:
    # At First Logical Implemented Interfaces outside the Module
    # Process both includes and consists_of to capture nested components
    sub_components = need.get("includes", []) + need.get("consists_of", [])
    for need_inc in sub_components:
        curr_need = all_needs.get(need_inc, {})

        # check for misspelled include
        if not curr_need:
            logger.info(f"{need}: include with id {need_inc} could not be found")
            continue

        draw_impl_interface(curr_need, all_needs, local_impl_interfaces)

    # Find implemented logical interface of the components inside the module
    local_impl_interfaces.update(
        get_interface_from_component(need, "implements", all_needs)
    )

    return local_impl_interfaces


def _process_impl_interfaces(
    need: dict[str, str],
    all_needs: dict[str, dict[str, str]],
    proc_impl_interfaces: dict[str, list[str]],
    structure_text: str,
) -> str:
    """Handle implemented interfaces outside the boxes."""
    local_impl_interfaces = draw_impl_interface(need, all_needs, set())
    # Add all interfaces which are implemented by component to global list
    # and provide implementation
    for iface in local_impl_interfaces:
        # check for misspelled implements
        if not all_needs.get(iface, []):
            logger.info(f"{need}: implements {iface} could not be found")
            continue
        if not proc_impl_interfaces.get(iface, []):
            structure_text += gen_interface_element(iface, all_needs, True)
            # Mark interface as processed to avoid duplicate generation
            proc_impl_interfaces[iface] = [need["id"]]
    return structure_text


def _process_used_interfaces(
    need: dict[str, str],
    all_needs: dict[str, dict[str, str]],
    proc_impl_interfaces: dict[str, list[str]],
    proc_used_interfaces: dict[str, list[str]],
    local_impl_interfaces: list[str],
    structure_text: str,
    linkage_text: str,
) -> tuple[str, str]:
    """Handle all interfaces which are used by component."""
    for iface, comps in proc_used_interfaces.items():
        # Check if this interface has been processed at all (for structure generation)
        interface_structure_exists = iface in proc_impl_interfaces and len(proc_impl_interfaces[iface]) > 0
        
        if not interface_structure_exists:
            # Add implementing components and modules
            impl_comp_str = get_impl_comp_from_logic_iface(iface, all_needs)
            impl_comp = all_needs.get(impl_comp_str[0], {}) if impl_comp_str else ""

            if impl_comp:
                retval = get_hierarchy_text(impl_comp_str[0], all_needs)
                structure_text += retval[2]  # module open
                structure_text += retval[0]  # rest open
                structure_text += retval[1]  # rest close
                structure_text += retval[3]  # module close
                if iface not in local_impl_interfaces:
                    structure_text += gen_interface_element(iface, all_needs, True)
                    # Mark interface as processed to avoid duplicate generation
                    proc_impl_interfaces[iface] = [impl_comp_str[0]]
                # Draw connection between implementing components and interface
                linkage_text += f"{
                    gen_link_text(impl_comp, '-u->', all_needs[iface], 'implements')
                } \n"
            else:
                # Add only interface if component not defined
                print(f"{iface}: No implementing component defined")
                structure_text += gen_interface_element(iface, all_needs, True)
                # Mark interface as processed to avoid duplicate generation
                proc_impl_interfaces[iface] = []

        # Interface can be used by multiple components
        for comp in comps:
            linkage_text += f"{
                gen_link_text(all_needs[comp], '-d[#green]->', all_needs[iface], 'uses')
            } \n"

    return structure_text, linkage_text


def draw_module(
    need: dict[str, str],
    all_needs: dict[str, dict[str, str]],
    proc_impl_interfaces: dict[str, list[str]],
    proc_used_interfaces: dict[str, list[str]],
) -> tuple[str, str, dict[str, list[str]], dict[str, list[str]]]:
    """
    Drawing and parsing function of a component.

    Example:
        input:
            need: component_1
            all_needs: all_needs_dict
            processed_interfaces: set()
        return:
            # Part 1 Structure Text
            component "Component 1" as C1 {
            }
            interface "Component Interface 1" as CI1 {
            real operation 1 ()
            real operation 2 ()
            }

            interface "Logical Interface 1" as LI1 {
            Logical Operation 1
            Logical Operation 2
            }

            interface "Component Interface 3" as CI3 {
            real operation 5 ()
            real operation 6 ()
            }

            # Part 2 Linkage Text
            CI1 --> LI1: implements
            C1 --> CI1: implements
            C1 --> CI3: uses

            # Part 3 processed_interfaces
            {
             'real_interface_1',
             'real_interface_2',
             'logical_interface_1'
            }

            # Part 4 processed_interfaces
            {
             'logical_interface_1',
             'logical_interface_2'
            }

            Note: part 1 and 2 are returned as one text item separated by '\n'.
            They are interpreted and names are shortened here to aid readability.
    Returns:
        Tuple of 4 parts.
        (Structure Text, Linkage Text, Processed (Real Interfaces),
        Processed Logical Interfaces)
    """
    linkage_text = ""
    structure_text = ""

    # Draw all implemented interfaces outside the boxes
    local_impl_interfaces = draw_impl_interface(need, all_needs, set())
    structure_text = _process_impl_interfaces(
        need, all_needs, proc_impl_interfaces, structure_text
    )

    # Draw outer module
    structure_text += f"{gen_struct_element('package', need)}  {{\n"

    # Draw inner components recursively
    for need_inc in need.get("includes", []):
        curr_need = all_needs.get(need_inc, {})
        # check for misspelled include
        if not curr_need:
            logger.info(f"{need}: include with id {need_inc} could not be found")
            continue
        if curr_need["type"] not in ["comp", "mod"]:
            continue
        
        # Check if this component is a container (has consists_of)
        # If so, draw it with white-box view to show nested sub-components
        is_container = bool(curr_need.get("consists_of"))
        
        sub_structure, sub_linkage, proc_impl_interfaces, proc_used_interfaces = (
            draw_comp_incl_impl_int(
                curr_need, all_needs, proc_impl_interfaces, proc_used_interfaces,
                white_box_view=is_container
            )
        )
        structure_text += sub_structure
        linkage_text += sub_linkage

    # close outer component
    structure_text += f"}} /' {need['title']} '/ \n\n"

    # Note: Interface elements are already added in _process_impl_interfaces
    # No need to add them again here to avoid duplicates

    # Add all interfaces which are used by component
    structure_text, linkage_text = _process_used_interfaces(
        need,
        all_needs,
        proc_impl_interfaces,
        proc_used_interfaces,
        list(local_impl_interfaces),
        structure_text,
        linkage_text,
    )

    # Remove duplicate links
    linkage_text = "\n".join(set(linkage_text.split("\n"))) + "\n"

    return structure_text, linkage_text, proc_impl_interfaces, proc_used_interfaces


#       ╭──────────────────────────────────────────────────────────────────────────────╮
#       │                    Classes with hashing to enable caching                    │
#       ╰──────────────────────────────────────────────────────────────────────────────╯


class draw_full_feature:
    def __repr__(self):
        return "draw_full_feature" + " in " + scripts_directory_hash()

    def _collect_recursive_components(
        self,
        component_id: str,
        all_needs: dict[str, dict[str, str]],
        visited_components: set[str],
    ) -> set[str]:
        """Recursively collect all components that have relationships with the given component.
        
        This includes:
        - Components that use interfaces implemented by this component
        - Components that implement interfaces used by this component
        - All sub-components (via includes/consists_of)
        """
        if component_id in visited_components or component_id not in all_needs:
            return visited_components
            
        component = all_needs[component_id]
        visited_components.add(component_id)
        
        # Get all interfaces implemented by this component
        impl_interfaces = get_interface_from_component(component, "implements", all_needs)
        
        # Get all interfaces used by this component
        used_interfaces = get_interface_from_component(component, "uses", all_needs)
        
        # For each implemented interface, find components that use it
        for iface in impl_interfaces:
            if iface in all_needs:
                # Find all components that use this interface
                for need_id, need in all_needs.items():
                    if need.get("type") in ["comp", "comp_arc_sta"]:
                        comp_used_ifaces = get_interface_from_component(need, "uses", all_needs)
                        if iface in comp_used_ifaces and need_id not in visited_components:
                            self._collect_recursive_components(need_id, all_needs, visited_components)
        
        # For each used interface, find the implementing component
        for iface in used_interfaces:
            if iface in all_needs:
                impl_comps = get_impl_comp_from_logic_iface(iface, all_needs)
                for impl_comp_id in impl_comps:
                    if impl_comp_id not in visited_components:
                        self._collect_recursive_components(impl_comp_id, all_needs, visited_components)
        
        # Also include all sub-components
        for sub_comp_id in component.get("includes", []):
            if sub_comp_id in all_needs and all_needs[sub_comp_id].get("type") in ["comp", "comp_arc_sta"]:
                self._collect_recursive_components(sub_comp_id, all_needs, visited_components)
        
        for sub_comp_id in component.get("consists_of", []):
            if sub_comp_id in all_needs and all_needs[sub_comp_id].get("type") in ["comp", "comp_arc_sta"]:
                self._collect_recursive_components(sub_comp_id, all_needs, visited_components)
        
        return visited_components

    def _collect_interfaces_and_modules(
        self,
        need: dict[str, str],
        all_needs: dict[str, dict[str, str]],
        interfacelist: list[str],
        impl_comp: dict[str, list[str]],
        proc_modules: list[str],
        proc_impl_interfaces: dict[str, list[str]],
        proc_used_interfaces: dict[str, list[str]],
        structure_text: str,
        link_text: str,
    ) -> CollectResult:
        """Process interfaces and load modules for implementation."""
        # Start with ONLY the primary components from the feature's consists_of directive
        primary_components: set[str] = set(need.get("consists_of", []))
        
        # Primary interfaces are from the feature's includes directive
        primary_interfaces: set[str] = set(interfacelist)
        
        # Track all interfaces for the diagram
        all_related_interfaces: set[str] = set(interfacelist)
        
        # Components that directly implement primary interfaces (but aren't primary components)
        # These should be shown but their chains should NOT be followed
        # Only include them if they're from the local feature scope (not external baselibs)
        primary_interface_implementers: set[str] = set()
        for iface in primary_interfaces:
            if iface in all_needs:
                impl_comps = get_impl_comp_from_logic_iface(iface, all_needs)
                for comp_id in impl_comps:
                    if comp_id not in primary_components:
                        # Don't add external baselibs components that happen to implement primary interfaces
                        is_external_baselib = comp_id.startswith('comp__baselibs_') or comp_id.startswith('comp__os_')
                        if not is_external_baselib:
                            primary_interface_implementers.add(comp_id)
        
        # Collect interfaces used by ONLY primary components (these are secondary interfaces)
        # DO NOT collect interfaces used by primary interface implementers
        secondary_interfaces: set[str] = set()
        for comp_id in primary_components:
            if comp_id in all_needs:
                comp = all_needs[comp_id]
                used_ifaces = get_interface_from_component(comp, "uses", all_needs)
                secondary_interfaces.update(used_ifaces)
                all_related_interfaces.update(used_ifaces)
        
        # Now collect secondary components that are connected through secondary interface chains
        # Start by finding components that implement the secondary interfaces
        secondary_components: set[str] = set()
        visited_interfaces: set[str] = set()
        interfaces_to_process = list(secondary_interfaces)
        
        while interfaces_to_process:
            iface = interfaces_to_process.pop(0)
            if iface in visited_interfaces or iface not in all_needs:
                continue
            visited_interfaces.add(iface)
            
            # Find components that implement this secondary interface
            impl_comps = get_impl_comp_from_logic_iface(iface, all_needs)
            for comp_id in impl_comps:
                if comp_id not in primary_components and comp_id in all_needs:
                    secondary_components.add(comp_id)
                    # Only follow the chain further if this component is from the logging feature scope
                    # Stop the chain at external baselibs/framework components
                    # Check if the component ID suggests it's from an external base library
                    is_external_baselib = comp_id.startswith('comp__baselibs_') or comp_id.startswith('comp__os_')
                    
                    if not is_external_baselib:
                        # Add interfaces used by this secondary component to continue the chain
                        comp = all_needs[comp_id]
                        used_ifaces = get_interface_from_component(comp, "uses", all_needs)
                        for used_iface in used_ifaces:
                            if used_iface not in visited_interfaces and used_iface not in primary_interfaces:
                                interfaces_to_process.append(used_iface)
                                all_related_interfaces.add(used_iface)
        
        # Combine all components to display
        all_related_components = primary_components | secondary_components | primary_interface_implementers
        
        # Collect all modules that contain these components
        modules_to_draw: set[str] = set()
        for comp_id in all_related_components:
            # Skip finding modules for external baselibs components
            # We'll draw these components individually instead
            is_external_baselib = comp_id.startswith('comp__baselibs_') or comp_id.startswith('comp__os_')
            if not is_external_baselib:
                module = get_module(comp_id, all_needs)
                if module:
                    modules_to_draw.add(module)
        
        # Collect all components that are included in modules we're about to draw
        # BUT exclude primary components - those need to be in impl_comp even if in a module
        components_in_modules_only: set[str] = set()
        for module in modules_to_draw:
            if module in all_needs:
                module_includes = all_needs[module].get("includes", [])
                for comp_id in module_includes:
                    # Only add to exclusion list if NOT a primary component
                    if comp_id not in primary_components:
                        components_in_modules_only.add(comp_id)
        
        # Draw all collected modules
        for module in modules_to_draw:
            if module not in proc_modules:
                tmp, link_text, proc_impl_interfaces, proc_used_interfaces = (
                    draw_module(
                        all_needs[module],
                        all_needs,
                        proc_impl_interfaces,
                        proc_used_interfaces,
                    )
                )
                structure_text += tmp
                proc_modules.append(module)
        
        # Update impl_comp mapping for all related interfaces
        # Exclude ONLY non-primary components that were drawn as part of a module
        for iface in all_related_interfaces:
            if all_needs.get(iface):
                comps = get_impl_comp_from_logic_iface(iface, all_needs)
                if comps:
                    # Filter to include: components in our set AND not in modules-only exclusion list
                    filtered_comps = [c for c in comps 
                                     if c in all_related_components 
                                     and c not in components_in_modules_only]
                    if filtered_comps:
                        impl_comp[iface] = filtered_comps
            else:
                logger.info(f"{need}: Interface {iface} could not be found")
                
        return (
            structure_text,
            link_text,
            proc_impl_interfaces,
            proc_used_interfaces,
            impl_comp,
            proc_modules,
        )

    def _build_links(
        self,
        need: dict[str, str],
        all_needs: dict[str, dict[str, str]],
        original_feature_interfaces: list[str],
        all_interfaces: list[str],
        impl_comp: dict[str, list[str]],
        link_text: str,
    ) -> str:
        """Add actor-interface and interface-component relations."""
        # Draw links for all interfaces (including secondary ones)
        for iface in all_interfaces:
            if impl_comps := impl_comp.get(iface):
                # Add relation between Actor and ONLY original Feature Interfaces
                if iface in original_feature_interfaces:
                    link_text += f"{
                        gen_link_text(
                            {'id': 'Feature_User'}, '-d->', all_needs[iface], 'use'
                        )
                    } \n"

                # Add relation between interface and ALL implementing components
                for imcomp in impl_comps:
                    if imcomp in all_needs:
                        link_text += f"{
                            gen_link_text(
                                all_needs[imcomp],
                                '-u->',
                                all_needs[iface],
                                'implements',
                            )
                        } \n"
                    else:
                        logger.info(f"Component {imcomp} not found in all_needs")
            else:
                logger.info(f"{need}: Interface {iface} could not be found")
                continue
        return link_text

    def __call__(
        self, need: dict[str, str], all_needs: dict[str, dict[str, str]]
    ) -> str:
        interfacelist: list[str] = []
        impl_comp: dict[str, list[str]] = dict()
        # Store all Elements which have already been processed
        proc_impl_interfaces: dict[str, list[str]] = dict()
        proc_used_interfaces: dict[str, list[str]] = dict()
        proc_modules: list[str] = list()

        link_text = ""
        structure_text = (
            f'actor "Feature User" as {get_alias({"id": "Feature_User"})} \n'
        )

        # Define Feature as a package
        # structure_text += f"{gen_struct_element('package', need)} {{\n"

        # Add logical Interfaces / Interface Operations (aka includes)
        for need_inc in need.get("includes", []):
            # Generate list of interfaces since both interfaces
            # and interface operations can be included
            iface = get_interface_from_int(need_inc, all_needs)
            if iface not in interfacelist:
                interfacelist.append(iface)

        # Process interfaces and collect required modules
        (
            structure_text,
            link_text,
            proc_impl_interfaces,
            proc_used_interfaces,
            impl_comp,
            proc_modules,
        ) = self._collect_interfaces_and_modules(
            need,
            all_needs,
            interfacelist,
            impl_comp,
            proc_modules,
            proc_impl_interfaces,
            proc_used_interfaces,
            structure_text,
            link_text,
        )

        # Close Package
        # structure_text += f"}} /' {need['title']}  '/ \n\n"

        # Build all links between actor, interfaces, and components
        # Use all interfaces from impl_comp (which includes all related interfaces)
        all_interfaces = list(impl_comp.keys())
        link_text = self._build_links(
            need, all_needs, interfacelist, all_interfaces, impl_comp, link_text
        )

        # Remove duplicate links
        link_text = "\n".join(set(link_text.split("\n"))) + "\n"

        return gen_header() + structure_text + link_text


class draw_full_module:
    def __repr__(self):
        return "draw_full_module" + " in " + scripts_directory_hash()

    def __call__(
        self, need: dict[str, str], all_needs: dict[str, dict[str, str]]
    ) -> str:
        # Store all Elements which have already been processed
        proc_impl_interfaces: dict[str, list[str]] = dict()
        proc_used_interfaces: dict[str, list[str]] = dict()
        structure_text, linkage_text, proc_impl_interfaces, proc_used_interfaces = (
            draw_module(need, all_needs, proc_impl_interfaces, proc_used_interfaces)
        )

        return gen_header() + structure_text + linkage_text


class draw_full_component:
    def __repr__(self):
        return "draw_full_component" + " in " + scripts_directory_hash()

    def __call__(
        self, need: dict[str, str], all_needs: dict[str, dict[str, str]]
    ) -> str:
        structure_text, linkage_text, _, _ = draw_comp_incl_impl_int(
            need, all_needs, dict(), dict(), True
        )

        # Draw all implemented interfaces outside the boxes
        local_impl_interfaces = draw_impl_interface(need, all_needs, set())

        # Add all interfaces which are implemented by component to global list
        # and provide implementation
        for iface in local_impl_interfaces:
            # check for misspelled implements
            if not all_needs.get(iface, []):
                logger.info(f"{need}: implements {iface} could not be found")
                continue

            structure_text += gen_interface_element(iface, all_needs, True)

        return gen_header() + structure_text + linkage_text


class draw_full_interface:
    def __repr__(self):
        return "draw_full_interface" + " in " + scripts_directory_hash()

    def __call__(
        self, need: dict[str, str], all_needs: dict[str, dict[str, str]]
    ) -> str:
        structure_text = gen_interface_element(need["id"], all_needs, True)

        return structure_text + "\n"


CallableType = Callable[[dict[str, Any], dict[str, dict[str, Any]]], str]

draw_uml_function_context: dict[str, CallableType] = {
    "draw_interface": draw_full_interface(),
    "draw_module": draw_full_module(),
    "draw_component": draw_full_component(),
    "draw_feature": draw_full_feature(),
}
