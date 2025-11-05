"""
CoTer Core Module
Gestion du moteur de shell hybride (MANUAL/AUTO/AGENT modes)
"""

from .shell_engine import ShellMode, ShellEngine
from .history_manager import HistoryManager
from .builtins import BuiltinCommands
from .prompt_manager import PromptManager

__all__ = ['ShellMode', 'ShellEngine', 'HistoryManager', 'BuiltinCommands', 'PromptManager']
