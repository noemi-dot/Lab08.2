from database.distributore_DAO import DistributoreDAO

'''
    MODELLO:
    - Rappresenta la struttura dati
    - Si occupa di gestire lo stato dell'applicazione
    - Interagisce con il database
'''

class Model:
    def __init__(self):
        self._distributori = None
        self.load_distributori()

        self.__sequenza_ottima = []
        self.__costo_ottimo = -1

    def load_distributori(self):
        """ Carica tutti i distributori e li setta nella variabile self._distributori """
        self._distributori = DistributoreDAO.get_distributori()

    def get_prezzo_medio(self, mese:int):
        """
        Calcola, per ogni distributore, il prezzo medio al litro per il mese selezionato.
        :param mese: Mese selezionato (un intero da 1 a 12)
        :return: lista di tuple --> (nome del distributore, media), es. (Distributore A, 1.789)
        """
        # TODO
        risultato = []

        # Iteriamo su tutti i distributori (A e B)
        for distributore in self._distributori:
            # Sfrutto l'ORM del DTO per caricare i prezzi
            prezzi_distributore = distributore.get_prezzi()

            # Filtro solo i prezzi del mese richiesto (mysql-connector restituisce oggetti date, quindi uso .month)
            prezzi_mese = [p.prezzo_litro for p in prezzi_distributore if p.data.month == mese]

            # Calcolo della media matematica
            if len(prezzi_mese) > 0:
                media = sum(prezzi_mese) / len(prezzi_mese)
                risultato.append((distributore.nome, media))
            else:
                # Gestione dell'errore nel caso non ci siano prezzi per evitare divisioni per zero
                # Nel caso non ci siano prezzi per quel mese
                risultato.append((distributore.nome, 0.0))

        return risultato

    def get_sequenza_ottima(self, mese:int):
        """
        Calcola la sequenza ottimale di rifornimenti nei primi 7 giorni
        :return: sequenza di nomi distributore ottimale
        :return: costo ottimale (cioè quello minimizzato dalla sequenza scelta)
        """
        self.__sequenza_ottima = []
        self.__costo_ottimo = -1
        prezzi_settimana = self.__get_prezzi_prima_settimana_mese(mese)

        self.__ricorsione([], 1, None, 0, prezzi_settimana)

        # Traduci gli ID in nomi
        id_to_nome = {distributore.id: distributore.nome for distributore in self._distributori}
        sequenza_nomi = [f"Giorno {giorno}: {id_to_nome[i]}" for giorno, i in enumerate(self.__sequenza_ottima, start=1)]
        return sequenza_nomi, round(self.__costo_ottimo, 2)

    def __ricorsione(self, sequenza_parziale, giorno, ultimo_distributore, costo_corrente, prezzi_settimana):
        """ Implementa la ricorsione """
        # TODO
        # 🟢 A - Condizione Terminale: se abbiamo pianificato tutti e 7 i giorni (siamo al giorno 8)
        if giorno > 7:
            # Se è la prima soluzione trovata (-1) oppure se il costo è migliore del costo ottimo attuale
            if self.__costo_ottimo == -1 or costo_corrente < self.__costo_ottimo:
                self.__costo_ottimo = costo_corrente
                # Importante: fare una copia della lista (.copy() oppure list()), altrimenti per referenza si svuota!
                self.__sequenza_ottima = list(sequenza_parziale)
            return
        # 🟡 C (Filtro/Pruning) - Se il costo parziale attuale ha già superato o eguagliato
        # il costo ottimo trovato in precedenza, inutile continuare su questo ramo (taglio dell'albero).
        if self.__costo_ottimo != -1 and costo_corrente >= self.__costo_ottimo:
            return

        # Ciclo sui distributori possibili (le chiavi del dizionario, cioè A e B)
        for dist_id in prezzi_settimana.keys():

            # 🔵 B - Calcolo dei costi parziali
            # L'indice della lista parte da 0, quindi giorno 1 si trova a indice 0
            prezzo_litro = prezzi_settimana[dist_id][giorno - 1]
            costo_carburante = prezzo_litro * 100

            # Aggiungo i 5€ se cambio distributore rispetto al giorno precedente
            costo_spostamento = 0
            if ultimo_distributore is not None and ultimo_distributore != dist_id:
                costo_spostamento = 5

            nuovo_costo_corrente = costo_corrente + costo_carburante + costo_spostamento

            # Preparo il parametro per la ricorsione
            sequenza_parziale.append(dist_id)

            # Chiamata ricorsiva per il giorno successivo
            self.__ricorsione(sequenza_parziale, giorno + 1, dist_id, nuovo_costo_corrente, prezzi_settimana)

            # 🟣 D - Back-tracking (rimuovo l'ultimo elemento inserito prima di passare alla prossima iterazione)
            sequenza_parziale.pop()

    def __get_prezzi_prima_settimana_mese(self, mese: int):
        """
        Restituisce i prezzi dei primi 7 giorni del mese selezionato per ciascun distributore.
        :return: un dizionario: {id_distributore: [prezzo_giorno1, ..., prezzo_giorno7]}
        """
        # TODO
        prezzi_settimana = {}

        for distributore in self._distributori:
            prezzi_distributore = distributore.get_prezzi()

            # Filtro i prezzi per il mese richiesto e per i primi 7 giorni
            prezzi_prima_settimana = [p for p in prezzi_distributore if p.data.month == mese and p.data.day <= 7]

            # Ordino la lista in base al giorno, per sicurezza (assicura che l'indice 0 sia l'1 del mese, l'indice 6 sia il 7)
            prezzi_prima_settimana.sort(key=lambda p: p.data.day)

            # Estraggo solo il valore numerico del prezzo al litro
            prezzi_settimana[distributore.id] = [p.prezzo_litro for p in prezzi_prima_settimana]

        return prezzi_settimana