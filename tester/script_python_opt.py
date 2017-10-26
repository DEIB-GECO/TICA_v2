import sys
import tqdm

result_file = "results/pietro_culo_opt.txt"
max_distance = 10000
list_of_tf = [
    "ARID3A",
    "ATF1",
    "ATF3",
    "ATF4",
    "BHLHE40",
    "BRCA1",
    "CBX1",
    "CEBPB",
    "CEBPD",
    "CEBPZ",
    "CHD2",
    "CREB1",
    "CREM",
    "CTCF",
    "DNMT3B",
    "DROSHA",
    "ELF1",
    "EP300",
    "ESRRA",
    "ETV4",
    "EZH2",
    "FOSL2",
    "FOXA1",
    "FOXA2",
    "FOXK2",
    "GABP",
    "GABPA",
    "GATA4",
    "GTF2F1",
    "HBP1",
    "HCFC1",
    "HDAC2",
    "HHEX",
    "HLF",
    "HNF1A",
    "HNF4A",
    "HNF4G",
    "HNRNPLL",
    "HSF1",
    "IKZF1",
    "IRF3",
    "JUN",
    "JUND",
    "KAT2B",
    "MAFF",
    "MAFK",
    "MAX",
    "MAZ",
    "MBD1",
    "MBD4",
    "MNT",
    "MXI1",
    "MYBL2",
    "MYC",
    "NFE2L2",
    "NFIC",
    "NR2C2",
    "NR2F6",
    "NR3C1",
    "NRF1",
    "PBX2",
    "PLRG1",
    "POLR2A",
    "POLR2AphosphoS2",
    "POLR2AphosphoS5",
    "PPARGC1A",
    "RAD21",
    "RAD51",
    "RCOR1",
    "REST",
    "RFX5",
    "RNF2",
    "RXRA",
    "SIN3A",
    "SIN3B",
    "SMC3",
    "SOX13",
    "SP1",
    "SREBF1",
    "SRF",
    "SSRP1",
    "SUZ12",
    "TAF1",
    "TBP",
    "TCF7",
    "TCF7L2",
    "TEAD4",
    "TFAP4",
    "TGIF2",
    "USF1",
    "USF2",
    "YBX1",
    "YY1",
    "ZBTB33",
    "ZBTB40",
    "ZBTB7A",
    "ZHX2",
    "ZKSCAN1",
    "ZMYM3",
    "ZNF143",
    "ZNF207",
    "ZNF274",
    "ZNF384"
]


chrs = [str(i+1) for i in range(22)] + ["x"]
tfs = {}

for tf in tqdm.tqdm(list_of_tf):
    tfs[tf] = {"1":[], "2":[], "3":[], "4":[], "5":[], "6":[], "7":[], "8":[], "9":[], "10":[], "11":[], "12":[], "13":[], "14":[], "15":[], "16":[], "17":[], "18":[], "19":[], "20":[], "21":[], "22":[], "x":[]}
    for line in open("cutted_joined/"+tf):
        s = line.strip().split("\t")
        tss = set() if len(s) == 2 or s[2] == "" else set([int(t) for t in s[2].split(",")])
        c = s[0][3:].lower()
        tfs[tf][c].append((c,int(s[1]),tf,tss))

tot_region=0
for tf in tfs.keys():
    print(tf + "\t" + str(len(tfs[tf])))
    tot_region += len(tfs[tf])

outfile = open(result_file, "w")
mindist_pairs = []
considered_pairs = []
for x in list_of_tf:
    for y in list_of_tf:
        if x < y:
            considered_pairs.append((x,y))
            
if True:
    if True:
        for (tf1,tf2) in tqdm.tqdm(considered_pairs):
            for c in chrs:
                pairs_tf1 = set()
                pairs_tf2 = set()
                r1 = tfs[tf1][c]
                r2 = tfs[tf2][c]
                r = sorted(r1 + r2, key = lambda x : x[1])
                dist_a = set()
                dist_b = set()
                if len(r) >= 2:
                    reg = r[0]
                    suc = r[1]
                    if reg[2] != suc[2]:
                        d = [(suc[1], reg[1], suc[1] - reg[1], suc[3].intersection(reg[3])==set())]
                        if reg[2] == tf1:
                            [dist_a.add(x) for x in d if x[2] < max_distance]
                        else:
                            [dist_b.add(x) for x in d if x[2] < max_distance]
    
                    reg = r[-1]
                    prev = r[-2]
                    if reg[2] != prev[2]:
                        d = [(reg[1], prev[1], reg[1] - prev[1], prev[3].intersection(reg[3])==set())]
                        if reg[2] == tf1:
                            [dist_a.add(x) for x in d if x[2] < max_distance]
                        else:
                            [dist_b.add(x) for x in d if x[2] < max_distance]

                for i in range(len(r))[1:-1]:
                    reg = r[i]
                    prev = r[i-1]
                    suc = r[i+1]
                    d=[]

                    if reg[2] == prev[2] and reg[2] == suc[2]:
                        pass
                    elif reg[2] == prev[2]:
                        d = [(suc[1], reg[1], suc[1] - reg[1], suc[3].intersection(reg[3])==set())]
                    elif reg[2] == suc[2]:
                        d = [(reg[1], prev[1], reg[1] - prev[1], prev[3].intersection(reg[3])==set())]
                    else:
                        d1 = (suc[1], reg[1], suc[1] - reg[1], suc[3].intersection(reg[3])==set())
                        d2 = (reg[1], prev[1], reg[1] - prev[1], prev[3].intersection(reg[3])==set())
                        if d1[2] < d2[2]:
                            d = [d1]
                        elif d2[2] < d1[2]:
                            d = [d2]
                        else:
                            d = [d1, d2]
                    if reg[2] == tf1:
                        [dist_a.add(x) for x in d if x[2] < max_distance]
                    else:
                        [dist_b.add(x) for x in d if x[2] < max_distance]
                for x in dist_a.intersection(dist_b):

                    outfile.write("\t".join([tf1, tf2, str(x[2]), str(int(x[3]))]) + "\n")

outfile.close()



