# -*- coding: utf-8 -*-
"""
Controlador de Borrado Diferido (Deshacer) para DespensAPP.
Los elementos se ocultan al instante y se eliminan de la base de datos tras una
ventana de gracia; si el usuario pulsa "Deshacer" no se borra nada.
"""

from typing import Callable, Dict, Optional, Tuple

UNDO_SECONDS = 4.0


class UndoController:
    """Cola de borrados pendientes con confirmación diferida."""

    def __init__(self, scheduler: Callable, delay: float = UNDO_SECONDS):
        """
        scheduler: función compatible con Clock.schedule_once(callback, timeout)
                   que retorna un evento con método cancel().
        """
        self.scheduler = scheduler
        self.delay = delay
        # (tipo, id) -> (evento_programado, función_que_borra, función_que_refresca)
        self._pending: Dict[Tuple[str, int], Tuple[object, Callable, Optional[Callable]]] = {}

    def schedule(self, kind: str, item_id: int, commit: Callable, on_done: Optional[Callable] = None):
        """Registra un borrado pendiente; se ejecutará tras `delay` segundos salvo que se deshaga."""
        key = (kind, item_id)
        if key in self._pending:
            return
        event = self.scheduler(lambda dt: self.commit(kind, item_id), self.delay)
        self._pending[key] = (event, commit, on_done)

    def undo(self, kind: str, item_id: int) -> bool:
        """Cancela el borrado pendiente. Retorna True si había algo que deshacer."""
        entry = self._pending.pop((kind, item_id), None)
        if not entry:
            return False
        event, _, on_done = entry
        if event is not None and hasattr(event, "cancel"):
            event.cancel()
        if on_done:
            on_done()
        return True

    def commit(self, kind: str, item_id: int):
        """Ejecuta ya el borrado real de un elemento pendiente."""
        entry = self._pending.pop((kind, item_id), None)
        if not entry:
            return
        event, commit, on_done = entry
        if event is not None and hasattr(event, "cancel"):
            event.cancel()
        try:
            commit()
        finally:
            if on_done:
                on_done()

    def flush(self):
        """Confirma todos los borrados pendientes (al cerrar sesión o la app)."""
        for kind, item_id in list(self._pending.keys()):
            self.commit(kind, item_id)

    def is_pending(self, kind: str, item_id: int) -> bool:
        return (kind, item_id) in self._pending

    def has_pending(self) -> bool:
        return bool(self._pending)
