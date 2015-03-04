def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ips = x_forwarded_for.split(',')

        for ip in ips:
            if 'unknown' not in ip:
                return ip.strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip
