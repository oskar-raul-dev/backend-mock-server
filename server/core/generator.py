"""
Response generation logic for the mockserver.

This module implements the ResponseGenerator class which handles the generation of
HTTP responses from response definitions. It provides Jinja2-based templating to
create dynamic responses based on request data.

Key Features:
    - Load response bodies from files or inline definitions
    - Jinja2 template rendering for both headers and body
    - Access to request context variables in templates
    - Automatic template variable injection

Template Variables Available:
    All response body and header values can use Jinja2 templates with these variables:
    - PATH_PARAMS: List of URL regex capture groups
    - QUERY_PARAMS: Dict of query parameters from URL
    - HEADERS: Dict of request headers (case-insensitive)
    - BODY: Raw request body string
    - BODY_PROCESSED: Parsed/processed body data (if processor was configured)

Example template usage in response body:
    ```json
    {
        "user_id": "{{ PATH_PARAMS[0] }}",
        "name": "{{ QUERY_PARAMS.name }}",
        "email": "{{ BODY_PROCESSED.email }}"
    }
    ```
"""
from pathlib import Path
from typing import Dict, Tuple
import jinja2

from .models import ResponseDef, RequestContext


class ResponseGenerator:
    """
    Generates HTTP responses from response definitions with Jinja2 templating.

    The ResponseGenerator takes a ResponseDef and RequestContext and produces a complete
    HTTP response (status, headers, body). It supports both inline body content and
    loading body templates from files.

    All response body and header values are processed as Jinja2 templates, allowing
    dynamic content based on the incoming request. Template variables come from the
    RequestContext extracted during request matching.

    Jinja2 Configuration:
        - autoescape: False (no HTML escaping, responses can be any format)
        - undefined: jinja2.Undefined (missing variables render as empty string)

    Example:
        >>> generator = ResponseGenerator()
        >>> response_def = ResponseDef(
        ...     status=200,
        ...     headers={"Content-Type": "application/json"},
        ...     body='{"user": "{{ PATH_PARAMS[0] }}", "action": "{{ QUERY_PARAMS.action }}"}'
        ... )
        >>> context = RequestContext(
        ...     PATH_PARAMS=["john"],
        ...     QUERY_PARAMS={"action": "login"},
        ...     HEADERS={},
        ...     BODY=None
        ... )
        >>> status, headers, body = generator.render(response_def, context, "config/")
        >>> print(status)  # 200
        >>> print(body)  # {"user": "john", "action": "login"}
    """

    def __init__(self):
        """
        Initialize response generator with Jinja2 environment.

        Creates a Jinja2 environment configured for mockserver template rendering:
        - No HTML autoescaping (supports JSON, XML, plain text, etc.)
        - Undefined variables are silently ignored (render as empty string)
        """
        self.jinja_env = jinja2.Environment(
            autoescape=False,
            undefined=jinja2.Undefined
        )

    def load_body_template(self, response_def: ResponseDef, responses_dir: str) -> str:
        """
        Load response body template from file or inline definition.

        The body template can come from two sources:
        1. File (body_file): Load content from file in responses_dir
        2. Inline (body): Use the body string directly

        If both are specified, body_file takes precedence.
        If neither is specified, returns empty string.

        Args:
            response_def: Response definition with body or body_file
            responses_dir: Base directory for resolving body_file paths

        Returns:
            Response body template as string (may contain Jinja2 syntax)

        Example:
            >>> # With inline body
            >>> response_def = ResponseDef(body='{"status": "ok"}')
            >>> template = generator.load_body_template(response_def, "config/")
            >>> print(template)  # {"status": "ok"}

            >>> # With body file
            >>> response_def = ResponseDef(body_file="welcome.html")
            >>> template = generator.load_body_template(response_def, "config/responses/")
            >>> # Returns content of config/responses/welcome.html
        """
        if response_def.body_file:
            file_path = Path(responses_dir) / response_def.body_file
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

        elif response_def.body:
            return response_def.body

        return ""

    def render(
        self,
        response_def: ResponseDef,
        context: RequestContext,
        responses_dir: str
    ) -> Tuple[int, Dict[str, str], str]:
        """
        Render a complete HTTP response with Jinja2 template variables from context.

        This is the main method that generates the final HTTP response. It:
        1. Loads the body template (from file or inline)
        2. Renders body with Jinja2 using context variables
        3. Renders each header value with Jinja2 using context variables
        4. Returns complete response tuple

        All template rendering has access to these variables from RequestContext:
            - PATH_PARAMS: URL regex capture groups (list)
            - QUERY_PARAMS: Query string parameters (dict)
            - HEADERS: Request headers (dict)
            - BODY: Raw request body (string or None)
            - BODY_PROCESSED: Processed body from processor callback (dict or None)

        Args:
            response_def: Response definition (status, headers, body/body_file)
            context: Request context containing template variables
            responses_dir: Base directory for loading body_file

        Returns:
            Tuple of (status_code, rendered_headers, rendered_body)
            - status_code: HTTP status code (int)
            - rendered_headers: Dict of header name -> rendered value (str)
            - rendered_body: Rendered body content (str)

        Example with path params:
            >>> response_def = ResponseDef(
            ...     status=200,
            ...     headers={"Content-Type": "application/json"},
            ...     body='{"id": "{{ PATH_PARAMS[0] }}", "name": "{{ PATH_PARAMS[1] }}"}'
            ... )
            >>> context = RequestContext(
            ...     PATH_PARAMS=["123", "john"],
            ...     QUERY_PARAMS={},
            ...     HEADERS={},
            ...     BODY=None
            ... )
            >>> status, headers, body = generator.render(response_def, context, "config/")
            >>> print(body)  # {"id": "123", "name": "john"}

        Example with processed body:
            >>> response_def = ResponseDef(
            ...     status=200,
            ...     body='User email: {{ BODY_PROCESSED.email }}'
            ... )
            >>> context = RequestContext(
            ...     PATH_PARAMS=[],
            ...     QUERY_PARAMS={},
            ...     HEADERS={},
            ...     BODY='{"email": "john@example.com"}',
            ...     BODY_PROCESSED={"email": "john@example.com"}
            ... )
            >>> status, headers, body = generator.render(response_def, context, "config/")
            >>> print(body)  # User email: john@example.com
        """
        template_vars = {
            'PATH_PARAMS': context.PATH_PARAMS,
            'QUERY_PARAMS': context.QUERY_PARAMS,
            'HEADERS': context.HEADERS,
            'BODY': context.BODY,
            'BODY_PROCESSED': context.BODY_PROCESSED
        }

        body_template_str = self.load_body_template(response_def, responses_dir)
        body_template = self.jinja_env.from_string(body_template_str)
        rendered_body = body_template.render(**template_vars)

        rendered_headers = {}
        for key, value_template in response_def.headers.items():
            template = self.jinja_env.from_string(value_template)
            rendered_headers[key] = template.render(**template_vars)

        return (response_def.status, rendered_headers, rendered_body)
