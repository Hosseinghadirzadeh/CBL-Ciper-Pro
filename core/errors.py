class LBCError(Exception):
    """Safe, user-displayable base error."""


class AuthenticationError(LBCError):
    pass


class CorpusError(LBCError):
    pass


class ContainerError(LBCError):
    pass


class MetadataError(LBCError):
    pass

