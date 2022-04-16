#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>

#include <X11/Xlib.h>


#include <signal.h>

#define BUFFER_LEN 1000

// #define DEBUG

static volatile int keepRunning = 1;

int catcher() {
    // Display* disp, XErrorEvent* xe
    // No window
#ifdef DEBUG
    printf("=== Catched error ===\n");
    printf("Catched error : %d\n", xe->type);
    printf("Catched error : %lu\n", xe->resourceid);
    printf("Catched error : %lu\n", xe->serial);
    printf("Catched error : %lu\n", xe->error_code);
    printf("Catched error : %lu\n", xe->request_code);
    printf("Catched error : %lu\n", xe->minor_code);
    printf("=== Catched error ===\n");
    fflush(fdebug);
#endif
    return 0;
}

unsigned char* get_string_property(Display* display, Window* window, char* property_name) {
    Atom actual_type, filter_atom;
    int actual_format, status;
    unsigned long nitems, bytes_after;
    unsigned char* prop;

    filter_atom = XInternAtom(display, property_name, True);
    status = XGetWindowProperty(display, *window, filter_atom, 0, BUFFER_LEN, False, AnyPropertyType,
        &actual_type, &actual_format, &nitems, &bytes_after, &prop);

    if (status == BadWindow) return (unsigned char*)""; // window id # 0x%lx does not exists
    else if (status != Success) return (unsigned char*)""; // XGetWindowProperty failed!
    else return prop;
}

long get_long_property(Display* display, Window* window, char* property_name) {
    unsigned char* prop = get_string_property(display, window, property_name);
    if (!strcmp((char*)prop, "")) return -1;

    long long_property = prop[0] + (prop[1] << 8) + (prop[2] << 16) + (prop[3] << 24);
    XFree(prop);
    return long_property;
}


// void printkey(Display* display, XEvent ev) {
    // KeySym touche, keysym;
    // char caractere[10], modifiers[40];
    // int nbre;

    // int nbre_keysym, i;
    // nbre = XLookupString(&ev, caractere, 10, &touche, 0);
    // // XKbKeycodeToKeysym
    // caractere[nbre] = '\0';
    // printf("Le keycode est %d (0x%x), le keysym est %d (0x%x)\n",
    //     ev.xkey.keycode, ev.xkey.keycode,
    //     XKeysymToString(touche), touche);
    // if (nbre == 0)
    //     printf("La chaine ascii correspondante est vide\n");
    // else
    //     printf("La chaine ascii obtenue est %s\n", caractere);
    // modifiers[0] = '\0';
    // if (ev.xkey.state & ShiftMask)
    //     strcat(modifiers, "Shift ");
    // if (ev.xkey.state & LockMask)
    //     strcat(modifiers, "Lock ");
    // if (ev.xkey.state & ControlMask)
    //     strcat(modifiers, "Control ");
    // if (ev.xkey.state & Mod1Mask)
    //     strcat(modifiers, "Mod1 ");
    // if (ev.xkey.state & Mod2Mask)
    //     strcat(modifiers, "Mod2 ");
    // if (ev.xkey.state & Mod3Mask)
    //     printf("Aucun modifier actif\n");
    // else
    //     printf("Modifiers actifs %s\n", modifiers);
    // printf("Les keysyms associes : ");
    // for (i = 0; i < nbre_keysym; ++i){
    //     if ((keysym = XKeycodeToKeysym(display, ev.xkey.keycode, i))
    //         == NoSymbol)
    //         printf("NoSymbol ");
    //     else
    //         printf("%s ", XKeysymToString(keysym));
    // }
    // printf("\n\n");
// }

void SIGINT_handler() {
    printf("closing...\n");
    // -fno-stack-protector
    keepRunning = 0;
}

int main(void) {
    Display* display = XOpenDisplay(NULL);
    Window root = XDefaultRootWindow(display);
    Window window;

    XSelectInput(display, root, PropertyChangeMask);

    XEvent ev;

    time_t t = time(NULL);
    struct tm* tm = localtime(&t);

    char* start_time = asctime(tm);
    printf("Starting at %s\n", start_time);

    char time_sec[12];
    struct timeval time_milisec;

    char* last_name = NULL;
    unsigned char* name;

    unsigned char* data;

    char* proc_path = malloc(sizeof(char) * BUFFER_LEN);
    char* comm = malloc(sizeof(char) * BUFFER_LEN);


    Atom type;
    int format;
    unsigned long items, bytes_left;

    long pid = 0;
    FILE* fp;

    char* fk_filepath = malloc(sizeof(char) * BUFFER_LEN);
    char* fd_filepath = malloc(sizeof(char) * BUFFER_LEN);

    strftime(time_sec, BUFFER_LEN, "%d-%m-%Y_%Hh%Mm%S", tm);
    sprintf(fk_filepath, "%s.keys", time_sec);
    sprintf(fd_filepath, "%s.wins", time_sec);

    FILE* fk = fopen(fk_filepath, "w");
    FILE* fd = fopen(fd_filepath, "w");

    free(fk_filepath);
    free(fd_filepath);

    fprintf(fd, "Starting at %s\n", start_time);

    signal(SIGINT, SIGINT_handler);
    XSetErrorHandler(catcher);

    while (keepRunning) {

        XNextEvent(display, &ev);

        if (!keepRunning)
            break;

        // printf("Event Type  : %d\n", ev.type);

        if (ev.type == ButtonPress) continue;

        if (ev.type == ButtonRelease) {
            name = get_string_property(display, &window, "_NET_WM_NAME");
            if (strcmp(last_name, (char*)name) != 0) {
                last_name = strdup((char*)name);
                gettimeofday(&time_milisec, NULL);

                fprintf(fd, "[%ld-%03lu] [%05lu] [%s] %s\n", time_milisec.tv_sec, ev.xkey.time % 1000, pid, comm, name);
                fflush(fd);
            }
            XFree(name);
        }


        if (ev.type == KeyRelease) continue;

        if (ev.type == KeyPress) {
            // printf("KEY          : %d\n", ev.xkey.type);
            // printf("KEY Time     : %lu\n", ev.xkey.time); // TIME OF EVENT
            // printf("KEY Time     : %lu\n", ev.xkey.time % 1000); // TIME OF EVENT
            // printf("KEY Position : %d_%d\n", ev.xkey.x, ev.xkey.y);
            // printf("KEY State    : %u\n", ev.xkey.state);

            // printf("KEY keycode  : %u\n", ev.xkey.keycode);
            fprintf(fk, "%u\n", ev.xkey.keycode);
            fflush(fk);

            name = get_string_property(display, &window, "_NET_WM_NAME");
            if (strcmp(last_name, (char*)name) != 0) {
                last_name = strdup((char*)name);
                gettimeofday(&time_milisec, NULL);

                fprintf(fd, "[%ld-%03lu] [%05lu] [%s] %s\n", time_milisec.tv_sec, ev.xkey.time % 1000, pid, comm, name);
                fflush(fd);
            }
            XFree(name);
        }

        if (ev.type == PropertyNotify) {
            char* atom;
            atom = XGetAtomName(display, ev.xproperty.atom);
            if (strcmp("_NET_ACTIVE_WINDOW", atom) == 0) {

                int status = XGetWindowProperty(display, root, ev.xproperty.atom, 0, 1, False, AnyPropertyType,
                    &type, &format, &items, &bytes_left, &data);

                if (status != Success) {
                    keepRunning = 0;
                    printf("XGetWindowProperty Failed !");
                    break;
                }
                if (!items) {
                    XFree(data);
                    keepRunning = 0;
                    printf("XGetWindowProperty -> No window ??");
                    break;
                }

                window = ((Window*)data)[0];
                XFree(data);

                XSelectInput(display, window, KeyPressMask | ExposureMask);

                // printf("active window id: %u\n", *window);

                gettimeofday(&time_milisec, NULL);

                pid = get_long_property(display, &window, "_NET_WM_PID");
                if (pid == -1) { // BadWindow ERROR
                    fprintf(fd, "[%ld-%03lu] [%05d] [%s]\n", time_milisec.tv_sec, time_milisec.tv_usec / 1000, 0, "Desktop");
                    fflush(fd);
                }
                else {
                    name = get_string_property(display, &window, "_NET_WM_NAME");
                    free(last_name);
                    last_name = strdup((char*)name);

                    // printf("WM_CLASS: %s\n", get_string_property(display, window, "WM_CLASS"));

                    sprintf(proc_path, "/proc/%ld/comm", pid);

                    fp = fopen(proc_path, "r");
                    comm = strtok(fgets(comm, BUFFER_LEN, fp), "\n");
                    fclose(fp);

                    fprintf(fd, "[%ld-%03lu] [%05lu] [%s] %s\n", time_milisec.tv_sec, time_milisec.tv_usec / 1000, pid, comm, name);
                    fflush(fd);

                    XFree(name);
                }
            }
            XFree(atom);
        }
    }
    printf("closing !\n");
    fclose(fk);
    fclose(fd);

    free(comm);
    free(proc_path);

    XSetErrorHandler(NULL);
    XFree(&window);
    XCloseDisplay(display);
    // XFree(display);
    printf("closed!\n");
}