#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import Any
import json

class GenreSelectionError(RuntimeError):
    pass

class GenreSelector:
    """Registry-backed genre selector plus lightweight menu/navigation surface.

    This module owns selection only. It never invents theory, instrumentation,
    performance behavior, or substitutes another genre.
    """
    def __init__(self, registry_path: str | Path, menu_path: str | Path | None = None):
        self.registry_path = Path(registry_path)
        self.registry = json.loads(self.registry_path.read_text())
        if self.registry.get('genre_selection_authority') != 'USER_ONLY':
            raise GenreSelectionError('GENRE_AUTHORITY_NOT_USER_ONLY')
        self.menu_path = Path(menu_path) if menu_path else None
        self.menu = json.loads(self.menu_path.read_text()) if self.menu_path else None
        self._validate_menu()

    def _validate_menu(self) -> None:
        if self.menu is None:
            return
        if self.menu.get('selection_authority') != 'USER_ONLY':
            raise GenreSelectionError('MENU_AUTHORITY_NOT_USER_ONLY')
        registered = self.registry.get('registered_genres', {})
        seen: set[str] = set()
        for group in self.menu.get('groups', []):
            for name in group.get('items', []):
                if name not in registered:
                    raise GenreSelectionError(f'MENU_GENRE_NOT_REGISTERED::{name}')
                if name in seen:
                    raise GenreSelectionError(f'MENU_DUPLICATE_GENRE::{name}')
                seen.add(name)

    def catalog(self) -> list[dict[str, Any]]:
        out = []
        detailed = self.registry.get('detailed_or_new_profiles', {})
        for name, status in self.registry.get('registered_genres', {}).items():
            profile = detailed.get(name, {})
            out.append({
                'genre_name': name,
                'status': status,
                'profile_id': profile.get('profile_id'),
                'execution_rule': profile.get('execution_rule'),
                'selectable': status != 'PARENT_NAVIGATION_ONLY',
            })
        return out

    def menu_groups(self) -> list[dict[str, Any]]:
        if self.menu is None:
            return []
        registered = self.registry.get('registered_genres', {})
        detailed = self.registry.get('detailed_or_new_profiles', {})
        result = []
        for group in self.menu.get('groups', []):
            items = []
            for name in group.get('items', []):
                status = registered[name]
                profile = detailed.get(name, {})
                items.append({
                    'genre_name': name,
                    'status': status,
                    'profile_id': profile.get('profile_id'),
                    'execution_rule': profile.get('execution_rule'),
                    'selectable': status != 'PARENT_NAVIGATION_ONLY' and not group.get('navigation_only', False),
                })
            result.append({
                'label': group['label'],
                'navigation_only': bool(group.get('navigation_only', False)),
                'items': items,
            })
        return result

    def select(self, genre_name: str) -> dict[str, Any]:
        registered = self.registry.get('registered_genres', {})
        if genre_name not in registered:
            raise GenreSelectionError('UNREGISTERED_GENRE')
        status = registered[genre_name]
        if status == 'PARENT_NAVIGATION_ONLY':
            raise GenreSelectionError('GENRE_CATEGORY_REQUIRES_CHILD_SELECTION')
        profile = self.registry.get('detailed_or_new_profiles', {}).get(genre_name, {})
        return {
            'genre_name': genre_name,
            'registry_status': status,
            'profile': profile,
            'selection_authority': 'USER_ONLY',
            'immutable_after_selection': True,
        }

    @staticmethod
    def _status_tag(item: dict[str, Any]) -> str:
        status = item['status']
        if item.get('profile_id') and status not in {'PROVISIONAL', 'PROVISIONAL_RESEARCH_REQUIRED', 'REGISTERED_PROFILE_RESEARCH_REQUIRED'}:
            return 'READY/PROFILED'
        if status in {'PROVISIONAL', 'PROVISIONAL_RESEARCH_REQUIRED', 'REGISTERED_PROFILE_RESEARCH_REQUIRED'}:
            return 'REGISTERED / NEEDS MORE PROFILE WORK'
        if status == 'EXISTING_THEORY_NEEDS_PERFORMANCE_BINDING':
            return 'REGISTERED / PERFORMANCE BINDING OPEN'
        if status == 'PARENT_NAVIGATION_ONLY':
            return 'CATEGORY'
        return 'REGISTERED'

    def render_text_menu(self) -> str:
        groups = self.menu_groups()
        lines = ['AI COMPOSITION — GENRE SELECTION', 'Choose one genre. Genre selection authority remains USER_ONLY.', '']
        choice = 1
        for group in groups:
            lines.append(f"[{group['label']}]")
            if group['navigation_only']:
                for item in group['items']:
                    lines.append(f"  — {item['genre_name']}  (family/navigation only)")
            else:
                for item in group['items']:
                    lines.append(f"  {choice:>2}. {item['genre_name']}  [{self._status_tag(item)}]")
                    choice += 1
            lines.append('')
        return '\n'.join(lines).rstrip()

    def numbered_choices(self) -> list[str]:
        choices = []
        for group in self.menu_groups():
            if group['navigation_only']:
                continue
            for item in group['items']:
                if item['selectable']:
                    choices.append(item['genre_name'])
        return choices

    def select_number(self, number: int) -> dict[str, Any]:
        choices = self.numbered_choices()
        if number < 1 or number > len(choices):
            raise GenreSelectionError('MENU_SELECTION_OUT_OF_RANGE')
        return self.select(choices[number - 1])

    def interactive(self) -> dict[str, Any]:
        print(self.render_text_menu())
        while True:
            raw = input('\nGenre number (or Q to quit): ').strip()
            if raw.lower() in {'q', 'quit', 'exit'}:
                raise GenreSelectionError('USER_CANCELLED')
            try:
                return self.select_number(int(raw))
            except (ValueError, GenreSelectionError):
                print('Please choose one of the numbered genre options.')

if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    registry = here / 'genre_registry_WORKING_GENRE_COMPLETE_2026-10-02_182810_CDT.json'
    menu = here / 'genre_menu_catalog_WORKING_2026-09-28.json'
    selector = GenreSelector(registry, menu)
    packet = selector.interactive()
    from engine import AICompositionEngine
    result = AICompositionEngine().run(packet['genre_name'])
    print('\nCOMPOSITION RESULT')
    print(json.dumps(result, indent=2))