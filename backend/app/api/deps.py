from ..container import Container, get_container
from ..services.ticket_service import TicketService


def get_container_dep() -> Container:
    return get_container()


def get_ticket_service() -> TicketService:
    return get_container().tickets
