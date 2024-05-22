# This is a copy of the GNU readline completer
# It has been changed to support completion of Airlock Gateway object attribute names

"""Word completion for GNU readline.

The completer completes keywords, built-ins and globals in a selectable
namespace (which defaults to __main__); when completing NAME.NAME..., it
evaluates (!) the expression up to the last dot and completes its attributes.

It's very cool to do "import sys" type "sys.", hit the completion key (twice),
and see the list of names defined by the sys module!

Tip: to use the tab key as the completion key, call

    readline.parse_and_bind("tab: complete")

Notes:

- Exceptions raised by the completer function are *ignored* (and generally cause
  the completion to fail).  This is a feature -- since readline sets the tty
  device in raw (or cbreak) mode, printing a traceback wouldn't work well
  without some complicated hoopla to save, reset and restore the tty state.

- The evaluation of the NAME.NAME... form may cause arbitrary application
  defined code to be executed if an object with a __getattr__ hook is found.
  Since it is the responsibility of the application (or the user) to enable this
  feature, I consider this an acceptable risk.  More complicated expressions
  (e.g. function calls or indexing operations) are *not* evaluated.

- When the original stdin is not a tty device, GNU readline is never
  used, and this module (and the readline module) are silently inactive.

"""

import atexit
import builtins
import __main__

from airscript.utils import cache

__all__ = ["Completer"]

airscriptTopKeywords = [
    'access',
    'aliasNames',
    'apiSecurity',
    'application',
    'backendPath',
    'certificate',
    'certificateChain',
    'defaultRedirect',
    'dosAttackPrevention',
    'downloadPdfsAsAttachmentsEnforced',
    'enableMaintenancePage',
    'encodedSlashesAllowed',
    'entryPath',
    'expertSettings',
    'hostName',
    'httpParameterPollutionDetection',
    'inBandChecks',
    'keepAliveTimeout',
    'kerberosEnvironmentId',
    'labels',
    'locking',
    'name',
    'networkInterface',
    'operationalMode',
    'outOfBandChecks',
    'pathRedirects',
    'privateKey',
    'requestBodyStreaming',
    'serverAdmin',
    'session',
    'showMaintenancePage',
    'strictlyMatchFullyQualifiedDomainName',
    'threatHandling',
    'timeouts',
    'tls',
]
airscriptAttributePaths = [
    'access.authenticationFlow',
    'access.authorizedRoles',
    'access.clientCertificateAuthentication',
    'access.credentialsPropagation.mandatory',
    'access.credentialsPropagation.type',
    'access.deniedUrl.mode',
    'access.deniedUrl.value',
    'access.ntlmPassthroughEnabled',
    'apiSecurity.logOnly',
    'apiSecurity.openApiEnforced',
    'application.backendLogoutUrl',
    'application.controlApiAllowed',
    'application.encryptedCookies.enabled',
    'application.encryptedCookies.prefix',
    'application.environmentCookiesEnabled',
    'application.loadBalancingCookieEnabled',
    'application.passthroughCookies.enabled',
    'application.passthroughCookies.prefix',
    'application.portalHeadersEnabled',
    'application.request.charset',
    'application.request.jsonParser.contentTypePattern.caseIgnored',
    'application.request.jsonParser.contentTypePattern.inverted',
    'application.request.jsonParser.contentTypePattern.pattern',
    'application.request.jsonParser.enabled',
    'application.response.body.rewrites',
    'application.response.compressionAllowed',
    'application.response.errorPage.rewrites',
    'application.response.header.location.rewrites',
    'application.response.html.rewrites',
    'application.response.stripCommentsEnabled',
    'application.sessionHandling',
    'application.webSocketsAllowed',
    'dosAttackPrevention.enabled',
    'dosAttackPrevention.interval',
    'dosAttackPrevention.maxRequestsPerInterval',
    'dosAttackPrevention.whitelistIpPattern.inverted',
    'dosAttackPrevention.whitelistIpPattern.pattern',
    'entryPath.ignoreCase',
    'entryPath.priority',
    'entryPath.regexFormatEnforced',
    'entryPath.value',
    'expertSettings.apache.enabled',
    'expertSettings.apache.settings',
    'expertSettings.securityGate.enabled',
    'expertSettings.securityGate.settings',
    'httpParameterPollutionDetection.mixedTypes.enabled',
    'httpParameterPollutionDetection.mixedTypes.logOnly',
    'httpParameterPollutionDetection.mixedTypes.parameterNameExceptionPattern.caseIgnored',
    'httpParameterPollutionDetection.mixedTypes.parameterNameExceptionPattern.inverted',
    'httpParameterPollutionDetection.mixedTypes.parameterNameExceptionPattern.pattern',
    'httpParameterPollutionDetection.sameType.enabled',
    'inBandChecks.checkResponseContentEnabled',
    'inBandChecks.contentPattern.caseIgnored',
    'inBandChecks.contentPattern.inverted',
    'inBandChecks.contentPattern.pattern',
    'inBandChecks.contentTypePattern.inverted',
    'inBandChecks.contentTypePattern.pattern',
    'inBandChecks.enabled',
    'inBandChecks.maxContentSize',
    'inBandChecks.statusPattern.enabled',
    'inBandChecks.statusPattern.inverted',
    'inBandChecks.statusPattern.pattern',
    'locking.access.authenticationFlow',
    'locking.access.authorizedRoles',
    'locking.access.clientCertificateAuthentication',
    'locking.access.credentialsPropagation.mandatory',
    'locking.access.credentialsPropagation.type',
    'locking.access.deniedUrl.mode',
    'locking.access.deniedUrl.value',
    'locking.access.ntlmPassthroughEnabled',
    'locking.apiSecurity.logOnly',
    'locking.apiSecurity.openApiDocumentId',
    'locking.apiSecurity.openApiEnforced',
    'locking.application.backendLogoutUrl',
    'locking.application.controlApiAllowed',
    'locking.application.encryptedCookies.enabled',
    'locking.application.encryptedCookies.prefix',
    'locking.application.environmentCookiesEnabled',
    'locking.application.loadBalancingCookieEnabled',
    'locking.application.passthroughCookies.enabled',
    'locking.application.passthroughCookies.prefix',
    'locking.application.portalHeadersEnabled',
    'locking.application.request.charset',
    'locking.application.request.jsonParser.contentTypePattern',
    'locking.application.request.jsonParser.enabled',
    'locking.application.response.body.rewrites',
    'locking.application.response.compressionAllowed',
    'locking.application.response.errorPage.rewrites',
    'locking.application.response.header.location.rewrites',
    'locking.application.response.html.rewrites',
    'locking.application.response.stripCommentsEnabled',
    'locking.application.sessionHandling',
    'locking.application.webSocketsAllowed',
    'locking.backendPath',
    'locking.dosAttackPrevention.enabled',
    'locking.dosAttackPrevention.interval',
    'locking.dosAttackPrevention.maxRequestsPerInterval',
    'locking.dosAttackPrevention.whitelistIpPattern',
    'locking.enabled',
    'locking.enableMaintenancePage',
    'locking.entryPath.priority',
    'locking.entryPath.regexFormatEnforced',
    'locking.entryPath.settings',
    'locking.httpParameterPollutionDetection.mixedTypes.enabled',
    'locking.httpParameterPollutionDetection.mixedTypes.logOnly',
    'locking.httpParameterPollutionDetection.mixedTypes.parameterNameExceptionPattern',
    'locking.httpParameterPollutionDetection.sameType.enabled',
    'locking.labels',
    'locking.operationalMode',
    'locking.requestBodyStreaming.contentTypePattern',
    'locking.requestBodyStreaming.enabled',
    'locking.requestBodyStreaming.httpMethodPattern',
    'locking.requestBodyStreaming.pathPattern',
    'locking.threatHandling',
    'locking.timeouts.backend',
    'locking.timeouts.sessionIdle',
    'networkInterface.externalLogicalInterfaceName',
    'networkInterface.http.enabled',
    'networkInterface.http.httpsRedirectEnforced',
    'networkInterface.http.port',
    'networkInterface.https.enabled',
    'networkInterface.https.http2Allowed',
    'networkInterface.https.port',
    'networkInterface.ipV4Address',
    'networkInterface.ipV6Address',
    'outOfBandChecks.checksWhenBad.interval',
    'outOfBandChecks.checksWhenBad.switchAfter',
    'outOfBandChecks.checksWhenGood.interval',
    'outOfBandChecks.checksWhenGood.switchAfter',
    'outOfBandChecks.contentPattern.caseIgnored',
    'outOfBandChecks.contentPattern.enabled',
    'outOfBandChecks.contentPattern.inverted',
    'outOfBandChecks.contentPattern.pattern',
    'outOfBandChecks.enabled',
    'outOfBandChecks.statusPattern.enabled',
    'outOfBandChecks.statusPattern.inverted',
    'outOfBandChecks.statusPattern.pattern',
    'outOfBandChecks.timeout',
    'outOfBandChecks.url',
    'requestBodyStreaming.contentTypePattern.caseIgnored',
    'requestBodyStreaming.contentTypePattern.inverted',
    'requestBodyStreaming.contentTypePattern.pattern',
    'requestBodyStreaming.enabled',
    'requestBodyStreaming.httpMethodPattern.caseIgnored',
    'requestBodyStreaming.httpMethodPattern.inverted',
    'requestBodyStreaming.httpMethodPattern.pattern',
    'requestBodyStreaming.pathPattern.caseIgnored',
    'requestBodyStreaming.pathPattern.inverted',
    'requestBodyStreaming.pathPattern.pattern',
    'session.cookieDomain',
    'session.cookiePath',
    'timeouts.backend',
    'timeouts.sessionIdle',
    'tls.caCertificatesForChainAndOcspValidation',
    'tls.caCertificatesForClientCertificateSelection',
    'tls.chainVerificationDepth',
    'tls.clientCertificateAuthentication',
    'tls.letsEncryptEnabled',
    'tls.lowStrengthCiphersAllowed',
    'tls.ocspStaplingEnabled',
    'tls.ocspValidationEnforced',
]


class Completer:
    def __init__(self, namespace = None):
        """Create a new completer for the command line.

        Completer([namespace]) -> completer instance.

        If unspecified, the default namespace where completions are performed
        is __main__ (technically, __main__.__dict__). Namespaces should be
        given as dictionaries.

        Completer instances should be used as the completion mechanism of
        readline via the set_completer() call:

        readline.set_completer(Completer(my_namespace).complete)
        """

        if namespace and not isinstance(namespace, dict):
            raise TypeError('namespace must be a dictionary')

        # Don't bind to namespace quite yet, but flag whether the user wants a
        # specific namespace or to use __main__.__dict__. This will allow us
        # to bind to __main__.__dict__ at completion time, not now.
        if namespace is None:
            self.use_main_ns = 1
        else:
            self.use_main_ns = 0
            self.namespace = namespace

    def complete(self, text, state):
        """Return the next possible completion for 'text'.

        This is called successively with state == 0, 1, 2, ... until it
        returns None.  The completion should begin with 'text'.

        """
        if self.use_main_ns:
            self.namespace = __main__.__dict__

        if not text.strip():
            if state == 0:
                if _readline_available:
                    readline.insert_text('\t')
                    readline.redisplay()
                    return ''
                else:
                    return '\t'
            else:
                return None

        if state == 0:
            if "." in text:
                self.matches = self.attr_matches(text)
            else:
                self.matches = self.global_matches(text)
        try:
            return self.matches[state]
        except IndexError:
            return None

    def _callable_postfix(self, val, word):
        if callable(val):
            word = word + "("
        return word

    def global_matches(self, text):
        """Compute matches when text is a simple name.

        Return a list of all keywords, built-in functions and names currently
        defined in self.namespace that match.

        """
        import keyword
        matches = []
        seen = {"__builtins__"}
        n = len(text)
        for word in keyword.kwlist:
            if word[:n] == text:
                seen.add(word)
                if word in {'finally', 'try'}:
                    word = word + ':'
                elif word not in {'False', 'None', 'True',
                                  'break', 'continue', 'pass',
                                  'else'}:
                    word = word + ' '
                matches.append(word)
        for nspace in [self.namespace, builtins.__dict__]:
            for word, val in nspace.items():
                if word[:n] == text and word not in seen:
                    seen.add(word)
                    matches.append(self._callable_postfix(val, word))
        for word in cache.getAttributeKeyNames():
            if word[:n] == text and word not in seen:
                seen.add(word)
                matches.append(word)
        return matches

    def attr_matches(self, text):
        """Compute matches when text contains a dot.

        Assuming the text is of the form NAME.NAME....[NAME], and is
        evaluable in self.namespace, it will be evaluated and its attributes
        (as revealed by dir()) are used as possible completions.  (For class
        instances, class members are also considered.)

        WARNING: this can still invoke arbitrary C code, if an object
        with a __getattr__ hook is evaluated.

        """
        matches = []
        n = len( text )
        for word in cache.getAttributeKeyPaths():
            if word[:n] == text:
                matches.append(word)
        
        import re
        m = re.match(r"(\w+(\.\w+)*)\.(\w*)", text)
        if not m:
            matches.sort()
            return matches
        expr, attr = m.group(1, 3)
        try:
            thisobject = eval(expr, self.namespace)
        except Exception:
            matches.sort()
            return matches

        # get the content of the object, except __builtins__
        words = set(dir(thisobject))
        words.discard("__builtins__")
        
        if hasattr(thisobject, '__class__'):
            words.add('__class__')
            words.update(get_class_members(thisobject.__class__))
        n = len(attr)
        if attr == '':
            noprefix = '_'
        elif attr == '_':
            noprefix = '__'
        else:
            noprefix = None
        while True:
            for word in words:
                if (word[:n] == attr and
                    not (noprefix and word[:n+1] == noprefix)):
                    match = "%s.%s" % (expr, word)
                    try:
                        val = getattr(thisobject, word)
                    except Exception:
                        pass  # Include even if attribute not set
                    else:
                        match = self._callable_postfix(val, match)
                    matches.append(match)
            if matches or not noprefix:
                break
            if noprefix == '_':
                noprefix = '__'
            else:
                noprefix = None
        matches.sort()
        return matches

def get_class_members(klass):
    ret = dir(klass)
    if hasattr(klass,'__bases__'):
        for base in klass.__bases__:
            ret = ret + get_class_members(base)
    return ret

try:
    import readline
except ImportError:
    _readline_available = False
else:
    readline.set_completer(Completer().complete)
    # Release references early at shutdown (the readline module's
    # contents are quasi-immortal, and the completer function holds a
    # reference to globals).
    atexit.register(lambda: readline.set_completer(None))
    _readline_available = True
